import hashlib
import json
from pathlib import Path
import sys

# Ensure repository root is on sys.path
REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

import pandas as pd

from backend.anomaly_detection import AnomalyScorer
from backend.cross_case_detection import HUB_DEGREE_THRESHOLD, discover_connections
from backend.fingerprint_engine import FingerprintEngine
from backend.graph_engine import load_transactions
from backend.similarity_engine import calibrate_threshold, compare_all, similarity


def generate_explanation(raw_a: dict, raw_b: dict, shared_count: int,
                         is_similar: bool, matching_feats: list) -> str:
    """Generates an honest explanation based on empirical feature comparisons.
    
    The term 'rapid' is only used if transaction timing (log_median_gap_min < 3.5)
    in both cases directly supports it.
    """
    # log_median_gap_min < 3.5 corresponds to median gap <= 32 minutes
    is_rapid_a = raw_a.get("log_median_gap_min", 0.0) < 3.5
    is_rapid_b = raw_b.get("log_median_gap_min", 0.0) < 3.5
    timing_rapid = is_rapid_a and is_rapid_b

    if is_similar:
        prefix = "Shares no common accounts. " if shared_count == 0 else f"Shares {shared_count} non-hub account(s). "
        timing_str = "rapid " if timing_rapid else ""
        split_a = int(raw_a.get("split_ratio", 0))
        split_b = int(raw_b.get("split_ratio", 0))
        hops_a = int(raw_a.get("hop_depth", 0))
        hops_b = int(raw_b.get("hop_depth", 0))
        detail = (f"Both cases demonstrate {timing_str}money movement with split fan-out "
                  f"({split_a} vs {split_b}) across {hops_a} hop(s).")
        return prefix + detail
    else:
        reasons = []
        if not timing_rapid:
            if not is_rapid_a and not is_rapid_b:
                reasons.append("transfer timing is prolonged rather than rapid")
            else:
                reasons.append("transfer speed differs significantly (rapid vs prolonged)")
        split_diff = abs(raw_a.get("split_ratio", 0) - raw_b.get("split_ratio", 0))
        if split_diff >= 1:
            reasons.append(f"fan-out structure differs (split ratio {int(raw_a.get('split_ratio', 0))} vs {int(raw_b.get('split_ratio', 0))})")
        hop_diff = abs(raw_a.get("hop_depth", 0) - raw_b.get("hop_depth", 0))
        if hop_diff >= 1:
            reasons.append(f"hop depth differs ({int(raw_a.get('hop_depth', 0))} vs {int(raw_b.get('hop_depth', 0))})")
        if not reasons:
            reasons.append("divergent feature distribution")
        return f"Behavioral profiles differ: {'; '.join(reasons)}."


def compute_evaluation_block(df: pd.DataFrame, gt: pd.DataFrame, filter_hubs: bool,
                             reported_ids: list, conn_map: dict) -> dict:
    engine = FingerprintEngine(df, filter_hubs=filter_hubs, hub_threshold=HUB_DEGREE_THRESHOLD)
    cal = calibrate_threshold(engine, gt)
    raw_pairs = compare_all(engine, reported_ids, cal["threshold"])

    pairs = []
    for p in raw_pairs:
        pair_key = tuple(sorted([p["case_a"], p["case_b"]]))
        shared_count = conn_map.get(pair_key, 0)
        raw_a = engine.features.loc[p["case_a"]].to_dict()
        raw_b = engine.features.loc[p["case_b"]].to_dict()
        explanation = generate_explanation(
            raw_a, raw_b, shared_count, p["is_similar"], p["matching_features"]
        )
        pairs.append({
            "case_a": p["case_a"],
            "case_b": p["case_b"],
            "similarity": p["similarity"],
            "is_similar": p["is_similar"],
            "shared_accounts": shared_count,
            "matching_features": p["matching_features"],
            "explanation": explanation
        })

    anomaly_scorer = AnomalyScorer(engine)
    reported_anomaly = {
        cid: round(anomaly_scorer.score(engine.fingerprints.loc[cid].values), 3)
        for cid in reported_ids
    }
    norm_ids = [c for c in engine.fingerprints.index if c.startswith("NORM_")]
    norm_anomaly = {
        cid: round(anomaly_scorer.score(engine.fingerprints.loc[cid].values), 3)
        for cid in norm_ids
    }
    mean_anomaly_reported = round(sum(reported_anomaly.values()) / len(reported_anomaly), 3)
    mean_anomaly_normal = round(sum(norm_anomaly.values()) / len(norm_anomaly), 3)

    matrix = {}
    for a in reported_ids:
        matrix[a] = {}
        for b in reported_ids:
            s = similarity(engine.fingerprints.loc[a].values, engine.fingerprints.loc[b].values)
            matrix[a][b] = round(float(s), 3)

    return {
        "hub_filter_active": filter_hubs,
        "calibration": {
            "threshold": cal["threshold"],
            "min_similar": cal["min_similar"],
            "max_dissimilar": cal["max_dissimilar"],
            "margin": cal["margin"]
        },
        "similarity_matrix": matrix,
        "anomaly_evaluation": {
            "mean_anomaly_reported": mean_anomaly_reported,
            "mean_anomaly_normal": mean_anomaly_normal,
            "reported_scores": reported_anomaly,
            "scaling_note": "Isolation Forest raw anomaly scores min-max normalized to [0.0, 1.0]; values are clipped at 1.0"
        },
        "pairs": pairs
    }


def run_export(output_path="evaluation/results/pattern_output.json"):
    df = load_transactions("dataset/transactions.csv")
    gt = pd.read_csv("dataset/ground_truth.csv")
    reported_ids = sorted(c for c in df.case_id.unique() if c.startswith("CASE_"))

    graph_conn = discover_connections(df, hub_threshold=HUB_DEGREE_THRESHOLD)
    conn_map = {}
    for c in graph_conn["connections"]:
        pair_key = tuple(sorted([c["case_a"], c["case_b"]]))
        conn_map[pair_key] = len(c["shared_accounts"])

    # Compute baseline results with hub filter ON (default)
    baseline_block = compute_evaluation_block(df, gt, True, reported_ids, conn_map)

    # Compute comparative results with hub filter OFF
    no_filter_block = compute_evaluation_block(df, gt, False, reported_ids, conn_map)

    out = {
        "hub_threshold": HUB_DEGREE_THRESHOLD,
        "hub_filter_active": True,
        "calibration": baseline_block["calibration"],
        "similarity_matrix": baseline_block["similarity_matrix"],
        "anomaly_evaluation": baseline_block["anomaly_evaluation"],
        "pairs": baseline_block["pairs"],
        "results_without_hub_filter": no_filter_block
    }

    out_file = Path(output_path)
    out_file.parent.mkdir(parents=True, exist_ok=True)
    with open(out_file, "w") as f:
        json.dump(out, f, indent=2, sort_keys=True)

    with open(out_file, "rb") as f:
        digest = hashlib.sha256(f.read()).hexdigest()

    print(f"Exported to {out_file} (SHA256: {digest})")
    return digest


if __name__ == "__main__":
    run_export()
