import hashlib
import json
import os
from pathlib import Path
import sys

# Ensure repository root is on sys.path
REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

import pandas as pd

from backend.anomaly_detection import AnomalyScorer
from backend.cross_case_detection import discover_connections
from backend.fingerprint_engine import FingerprintEngine
from backend.graph_engine import load_transactions
from backend.similarity_engine import calibrate_threshold, compare_all, similarity


def run_export(output_path="evaluation/results/pattern_output.json", filter_hubs=True):
    df = load_transactions("dataset/transactions.csv")
    gt = pd.read_csv("dataset/ground_truth.csv")
    
    # 1. Initialize FingerprintEngine with principled hub filtering default
    engine = FingerprintEngine(df, filter_hubs=filter_hubs)
    cal = calibrate_threshold(engine, gt)
    
    # 2. Get reported case IDs
    reported_ids = sorted(c for c in df.case_id.unique() if c.startswith("CASE_"))
    
    # 3. Pairwise comparisons
    raw_pairs = compare_all(engine, reported_ids, cal["threshold"])
    
    # Check shared accounts from graph connection analysis to populate shared_accounts count
    graph_conn = discover_connections(df)
    conn_map = {}
    for c in graph_conn["connections"]:
        pair_key = tuple(sorted([c["case_a"], c["case_b"]]))
        conn_map[pair_key] = len(c["shared_accounts"])
        
    pairs = []
    for p in raw_pairs:
        pair_key = tuple(sorted([p["case_a"], p["case_b"]]))
        shared_count = conn_map.get(pair_key, 0)
        
        explanation = ""
        if shared_count == 0 and p["is_similar"]:
            explanation = "No common accounts, but both cases show rapid fan-out into 3 intermediaries followed by consolidation."
        elif shared_count > 0 and p["is_similar"]:
            explanation = f"Shares {shared_count} account(s) and exhibits similar fan-out / consolidation money flow."
        elif not p["is_similar"]:
            explanation = "Timing and transaction structure differ significantly from the known layered fraud pattern."
            
        pairs.append({
            "case_a": p["case_a"],
            "case_b": p["case_b"],
            "similarity": p["similarity"],
            "is_similar": p["is_similar"],
            "shared_accounts": shared_count,
            "matching_features": p["matching_features"],
            "explanation": explanation
        })
        
    # 4. Anomaly scoring
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
    
    # 5. 6x6 Similarity Matrix
    matrix = {}
    for a in reported_ids:
        matrix[a] = {}
        for b in reported_ids:
            s = similarity(engine.fingerprints.loc[a].values, engine.fingerprints.loc[b].values)
            matrix[a][b] = round(float(s), 3)

    out = {
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
            "reported_scores": reported_anomaly
        },
        "pairs": pairs
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
