from datetime import datetime, timedelta
import hashlib
import json
from pathlib import Path
import sys

# Ensure repository root is on sys.path
REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

import numpy as np
import pandas as pd
from sklearn.preprocessing import StandardScaler

from backend.cross_case_detection import HUB_DEGREE_THRESHOLD
from backend.feature_extraction import FEATURES, case_features
from backend.fingerprint_engine import FingerprintEngine
from backend.graph_engine import load_transactions
from backend.similarity_engine import calibrate_threshold, similarity


def run_stress_tests(output_path="evaluation/results/stress_results.json"):
    df = load_transactions("dataset/transactions.csv")
    gt = pd.read_csv("dataset/ground_truth.csv")
    
    # Baseline engines
    eng_on = FingerprintEngine(df, filter_hubs=True, hub_threshold=HUB_DEGREE_THRESHOLD)
    cal_on = calibrate_threshold(eng_on, gt)
    thresh_on = cal_on["threshold"]

    eng_off = FingerprintEngine(df, filter_hubs=False)
    cal_off = calibrate_threshold(eng_off, gt)
    thresh_off = cal_off["threshold"]

    T0 = datetime(2026, 11, 1, 9, 0, 0)
    ACCT_BANK = {
        "B801": "Bank Beta",
        "B970": "Bank Beta",
        "A971": "Bank Alpha",
        "G972": "Bank Gamma",
        "G979": "Bank Gamma"  # Non-hub cash-out account
    }

    # =========================================================================
    # Stress Test 1: CASE_F Variants (Cash-out to Non-Hub, Speed 1 to 40)
    # =========================================================================
    def build_case_f_variant(speed: float) -> pd.DataFrame:
        rows = []
        t = T0 + timedelta(days=14)
        # Victim transfer into mule
        rows.append({
            "transaction_id": "STX_F_01",
            "case_id": "CASE_F_VAR",
            "sender_bank": ACCT_BANK["B801"],
            "receiver_bank": ACCT_BANK["B970"],
            "sender_account": "B801",
            "receiver_account": "B970",
            "amount": 26000.0,
            "timestamp": t,
            "transaction_type": "Transfer",
            "is_synthetic_suspicious": "Yes",
            "source": "synthetic"
        })
        t += timedelta(minutes=15.0 * speed)
        share = 26000.0 * 0.95 / 2
        fwd = []
        for i, m in enumerate(["A971", "G972"], start=2):
            rows.append({
                "transaction_id": f"STX_F_{i:02d}",
                "case_id": "CASE_F_VAR",
                "sender_bank": ACCT_BANK["B970"],
                "receiver_bank": ACCT_BANK[m],
                "sender_account": "B970",
                "receiver_account": m,
                "amount": share,
                "timestamp": t,
                "transaction_type": "Transfer",
                "is_synthetic_suspicious": "Yes",
                "source": "synthetic"
            })
            fwd.append((m, share, t))
            t += timedelta(minutes=5.0 * speed)
            
        for i, (m, amt, tt) in enumerate(fwd, start=4):
            t2 = tt + timedelta(minutes=25.0 * speed)
            rows.append({
                "transaction_id": f"STX_F_{i:02d}",
                "case_id": "CASE_F_VAR",
                "sender_bank": ACCT_BANK[m],
                "receiver_bank": ACCT_BANK["G979"],
                "sender_account": m,
                "receiver_account": "G979",  # Non-hub account
                "amount": amt * 0.97,
                "timestamp": t2,
                "transaction_type": "Transfer",
                "is_synthetic_suspicious": "Yes",
                "source": "synthetic"
            })
        var_df = pd.DataFrame(rows)
        var_df["timestamp"] = pd.to_datetime(var_df["timestamp"])
        return var_df

    speeds = [1, 2, 3, 5, 8, 10, 15, 20, 25, 30, 35, 40]
    case_f_speed_results = []
    crossover_on = None
    crossover_off = None

    for sp in speeds:
        var_df = build_case_f_variant(sp)
        # Filter ON evaluation
        feats_on = case_features(var_df, hub_accounts=eng_on.hub_accounts)
        z_on = eng_on.fingerprint_of(feats_on)
        sim_a_on = round(similarity(eng_on.fingerprints.loc["CASE_A"].values, z_on), 3)
        above_thresh_on = bool(sim_a_on >= thresh_on)
        if above_thresh_on and crossover_on is None:
            crossover_on = sp

        # Filter OFF evaluation
        feats_off = case_features(var_df, hub_accounts=None)
        z_off = eng_off.fingerprint_of(feats_off)
        sim_a_off = round(similarity(eng_off.fingerprints.loc["CASE_A"].values, z_off), 3)
        above_thresh_off = bool(sim_a_off >= thresh_off)
        if above_thresh_off and crossover_off is None:
            crossover_off = sp

        case_f_speed_results.append({
            "speed": sp,
            "filter_on": {
                "similarity_to_case_a": sim_a_on,
                "threshold": thresh_on,
                "above_threshold": above_thresh_on
            },
            "filter_off": {
                "similarity_to_case_a": sim_a_off,
                "threshold": thresh_off,
                "above_threshold": above_thresh_off
            }
        })

    # =========================================================================
    # Stress Test 2: CASE_D Noise (Amounts x0.6-1.6, Gaps x0.5-3.0)
    # =========================================================================
    case_d_df = df[df.case_id == "CASE_D"].copy().sort_values("timestamp")
    t0_d = case_d_df.timestamp.min()
    amt_multipliers = [0.6, 0.8, 1.0, 1.2, 1.4, 1.6]
    gap_multipliers = [0.5, 1.0, 1.5, 2.0, 2.5, 3.0]
    case_d_noise_results = []
    num_above_thresh = 0
    num_separating_controls = 0

    for amt_m in amt_multipliers:
        for gap_m in gap_multipliers:
            noisy = case_d_df.copy()
            noisy["amount"] = (noisy["amount"] * amt_m).round(2)
            time_offsets = (noisy["timestamp"] - t0_d) * gap_m
            noisy["timestamp"] = t0_d + time_offsets
            
            feats_d = case_features(noisy, hub_accounts=eng_on.hub_accounts)
            z_d = eng_on.fingerprint_of(feats_d)
            sim_a = round(similarity(eng_on.fingerprints.loc["CASE_A"].values, z_d), 3)
            sim_e = round(similarity(eng_on.fingerprints.loc["CASE_E"].values, z_d), 3)
            sim_f = round(similarity(eng_on.fingerprints.loc["CASE_F"].values, z_d), 3)
            
            above = bool(sim_a >= thresh_on)
            separates = bool(sim_a > max(sim_e, sim_f))
            if above:
                num_above_thresh += 1
            if separates:
                num_separating_controls += 1

            case_d_noise_results.append({
                "amount_multiplier": amt_m,
                "gap_multiplier": gap_m,
                "similarity_to_case_a": sim_a,
                "similarity_to_case_e": sim_e,
                "similarity_to_case_f": sim_f,
                "above_threshold": above,
                "separates_from_controls": separates
            })

    # =========================================================================
    # Stress Test 3: Feature Ablation (Excluding n_passthrough, hop_depth, retention)
    # =========================================================================
    ablated_feats = [f for f in FEATURES if f not in ["n_passthrough", "hop_depth", "retention"]]
    raw_ablated = eng_on.features[ablated_feats].values
    scaler_ab = StandardScaler().fit(raw_ablated)
    z_ab = pd.DataFrame(scaler_ab.transform(raw_ablated), index=eng_on.features.index, columns=ablated_feats)

    sims_ab, dis_ab = [], []
    for r in gt.itertuples():
        s = similarity(z_ab.loc[r.case_1].values, z_ab.loc[r.case_2].values)
        if r.expect_similar == "Yes":
            sims_ab.append(s)
        else:
            dis_ab.append(s)

    lo_ab, hi_ab = float(min(sims_ab)), float(max(dis_ab))
    thresh_ab = (lo_ab + hi_ab) / 2
    margin_ab = lo_ab - hi_ab

    # =========================================================================
    # Stress Test 4: False Flags at Threshold +-0.05 and Hub Thresholds 15, 25, 40
    # =========================================================================
    # Threshold sensitivity
    thresh_sensitivity = []
    for offset in [-0.05, 0.0, 0.05]:
        t_val = round(thresh_on + offset, 3)
        fps = []
        fns = []
        for r in gt.itertuples():
            s = similarity(eng_on.fingerprints.loc[r.case_1].values, eng_on.fingerprints.loc[r.case_2].values)
            if r.expect_similar == "No" and s >= t_val:
                fps.append({"pair": [r.case_1, r.case_2], "similarity": round(s, 3)})
            elif r.expect_similar == "Yes" and s < t_val:
                fns.append({"pair": [r.case_1, r.case_2], "similarity": round(s, 3)})
        thresh_sensitivity.append({
            "threshold_offset": offset,
            "threshold_value": t_val,
            "false_positive_count": len(fps),
            "false_positives": fps,
            "false_negative_count": len(fns),
            "false_negatives": fns
        })

    # Hub threshold sensitivity
    hub_threshold_sensitivity = []
    for ht in [15, 25, 40]:
        e_ht = FingerprintEngine(df, filter_hubs=True, hub_threshold=ht)
        cal_ht = calibrate_threshold(e_ht, gt)
        t_ht = cal_ht["threshold"]
        fps_ht = []
        fns_ht = []
        for r in gt.itertuples():
            s = similarity(e_ht.fingerprints.loc[r.case_1].values, e_ht.fingerprints.loc[r.case_2].values)
            if r.expect_similar == "No" and s >= t_ht:
                fps_ht.append({"pair": [r.case_1, r.case_2], "similarity": round(s, 3)})
            elif r.expect_similar == "Yes" and s < t_ht:
                fns_ht.append({"pair": [r.case_1, r.case_2], "similarity": round(s, 3)})
        hub_threshold_sensitivity.append({
            "hub_threshold": ht,
            "filtered_accounts": sorted(list(e_ht.hub_accounts)),
            "calibrated_threshold": cal_ht["threshold"],
            "margin": cal_ht["margin"],
            "min_similar": cal_ht["min_similar"],
            "max_dissimilar": cal_ht["max_dissimilar"],
            "false_positive_count": len(fps_ht),
            "false_positives": fps_ht,
            "false_negative_count": len(fns_ht),
            "false_negatives": fns_ht
        })

    out = {
        "stress_test_1_case_f_speed_sweep": {
            "description": "CASE_F variants whose cash-out goes to non-hub account G979 across speeds 1 to 40",
            "crossover_speed_filter_on": crossover_on,
            "crossover_speed_filter_off": crossover_off,
            "results": case_f_speed_results
        },
        "stress_test_2_case_d_noise": {
            "description": "CASE_D perturbed with amounts x0.6-1.6 and gaps x0.5-3.0 across 36 permutations",
            "total_permutations": len(case_d_noise_results),
            "permutations_above_threshold": num_above_thresh,
            "permutations_separating_from_controls": num_separating_controls,
            "min_similarity_to_case_a": min(r["similarity_to_case_a"] for r in case_d_noise_results),
            "max_similarity_to_case_a": max(r["similarity_to_case_a"] for r in case_d_noise_results),
            "results": case_d_noise_results
        },
        "stress_test_3_feature_ablation": {
            "description": "Feature ablation removing n_passthrough, hop_depth, and retention (12 features remaining)",
            "baseline_features_count": len(FEATURES),
            "ablated_features_count": len(ablated_feats),
            "baseline_margin": cal_on["margin"],
            "ablated_margin": round(margin_ab, 3),
            "baseline_threshold": cal_on["threshold"],
            "ablated_threshold": round(thresh_ab, 3),
            "ablated_min_similar": round(lo_ab, 3),
            "ablated_max_dissimilar": round(hi_ab, 3)
        },
        "stress_test_4_threshold_and_hub_sensitivity": {
            "threshold_sensitivity": thresh_sensitivity,
            "hub_threshold_sensitivity": hub_threshold_sensitivity
        }
    }

    out_file = Path(output_path)
    out_file.parent.mkdir(parents=True, exist_ok=True)
    with open(out_file, "w") as f:
        json.dump(out, f, indent=2, sort_keys=True)

    with open(out_file, "rb") as f:
        digest = hashlib.sha256(f.read()).hexdigest()

    print(f"Stress test results exported to {out_file} (SHA256: {digest})")
    return digest


if __name__ == "__main__":
    run_stress_tests()
