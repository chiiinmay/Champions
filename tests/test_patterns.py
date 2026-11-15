import numpy as np
import pandas as pd

from backend.feature_extraction import FEATURES, case_features
from backend.fingerprint_engine import FingerprintEngine
from backend.graph_engine import load_transactions
from backend.similarity_engine import calibrate_threshold, similarity

df = load_transactions("dataset/transactions.csv")
gt = pd.read_csv("dataset/ground_truth.csv")
eng = FingerprintEngine(df)
cal = calibrate_threshold(eng, gt)


def sim(a, b):
    return similarity(eng.fingerprints.loc[a].values, eng.fingerprints.loc[b].values)


def test_case_d_similar_to_a():
    """Missing Link test: CASE_D has identical behavior to CASE_A despite zero shared accounts."""
    assert sim("CASE_A", "CASE_D") >= cal["threshold"]


def test_controls_not_matched():
    """Controls test: CASE_E (slow transfer) and CASE_F (near miss) must not match CASE_A."""
    assert sim("CASE_A", "CASE_E") < cal["threshold"]
    assert sim("CASE_A", "CASE_F") < cal["threshold"]


def test_positive_margin():
    """Calibration margin must be strictly positive."""
    assert cal["margin"] > 0


def test_edge_case_single_transaction():
    """Edge case: Cluster with exactly 1 transaction. No feature should be NaN or infinite."""
    single_tx_df = pd.DataFrame([{
        "transaction_id": "TX_EDGE_1",
        "case_id": "CASE_EDGE_1",
        "sender_bank": "Bank Alpha",
        "receiver_bank": "Bank Beta",
        "sender_account": "EDGE_A",
        "receiver_account": "EDGE_B",
        "amount": 5000.0,
        "timestamp": pd.Timestamp("2026-11-01 10:00:00"),
        "transaction_type": "Transfer",
        "is_synthetic_suspicious": "No",
        "source": "synthetic"
    }])
    feats = case_features(single_tx_df)
    assert len(feats) == len(FEATURES)
    for k, v in feats.items():
        assert not np.isnan(v), f"Feature {k} is NaN"
        assert not np.isinf(v), f"Feature {k} is infinite"
    assert feats["n_tx"] == 1
    assert feats["hop_depth"] == 1
    assert feats["n_passthrough"] == 0
    assert feats["retention"] == 0.0


def test_edge_case_two_transactions():
    """Edge case: Cluster with exactly 2 transactions. No feature should be NaN or infinite."""
    two_tx_df = pd.DataFrame([
        {
            "transaction_id": "TX_EDGE_2A",
            "case_id": "CASE_EDGE_2",
            "sender_bank": "Bank Alpha",
            "receiver_bank": "Bank Beta",
            "sender_account": "EDGE_A",
            "receiver_account": "EDGE_B",
            "amount": 5000.0,
            "timestamp": pd.Timestamp("2026-11-01 10:00:00"),
            "transaction_type": "Transfer",
            "is_synthetic_suspicious": "No",
            "source": "synthetic"
        },
        {
            "transaction_id": "TX_EDGE_2B",
            "case_id": "CASE_EDGE_2",
            "sender_bank": "Bank Beta",
            "receiver_bank": "Bank Gamma",
            "sender_account": "EDGE_B",
            "receiver_account": "EDGE_C",
            "amount": 4800.0,
            "timestamp": pd.Timestamp("2026-11-01 10:15:00"),
            "transaction_type": "Transfer",
            "is_synthetic_suspicious": "No",
            "source": "synthetic"
        }
    ])
    feats = case_features(two_tx_df)
    assert len(feats) == len(FEATURES)
    for k, v in feats.items():
        assert not np.isnan(v), f"Feature {k} is NaN"
        assert not np.isinf(v), f"Feature {k} is infinite"
    assert feats["n_tx"] == 2
    assert feats["hop_depth"] == 2
    assert feats["n_passthrough"] == 1


def test_edge_case_no_passthrough():
    """Edge case: Cluster with no pass-through accounts (direct transfers)."""
    direct_df = pd.DataFrame([
        {
            "transaction_id": "TX_DIR_1",
            "case_id": "CASE_DIR",
            "sender_bank": "Bank Alpha",
            "receiver_bank": "Bank Beta",
            "sender_account": "DIR_A",
            "receiver_account": "DIR_B",
            "amount": 1000.0,
            "timestamp": pd.Timestamp("2026-11-01 10:00:00"),
            "transaction_type": "Transfer",
            "is_synthetic_suspicious": "No",
            "source": "synthetic"
        },
        {
            "transaction_id": "TX_DIR_2",
            "case_id": "CASE_DIR",
            "sender_bank": "Bank Alpha",
            "receiver_bank": "Bank Gamma",
            "sender_account": "DIR_C",
            "receiver_account": "DIR_D",
            "amount": 2000.0,
            "timestamp": pd.Timestamp("2026-11-01 10:05:00"),
            "transaction_type": "Transfer",
            "is_synthetic_suspicious": "No",
            "source": "synthetic"
        }
    ])
    feats = case_features(direct_df)
    assert len(feats) == len(FEATURES)
    for k, v in feats.items():
        assert not np.isnan(v), f"Feature {k} is NaN"
        assert not np.isinf(v), f"Feature {k} is infinite"
    assert feats["n_passthrough"] == 0
    assert feats["retention"] == 0.0


def test_edge_case_cycles():
    """Edge case: Graph with circular transfers (cycles). NetworkX cycle detection fallback must not crash."""
    cycle_df = pd.DataFrame([
        {
            "transaction_id": "TX_CYC_1",
            "case_id": "CASE_CYC",
            "sender_bank": "Bank Alpha",
            "receiver_bank": "Bank Beta",
            "sender_account": "CYC_A",
            "receiver_account": "CYC_B",
            "amount": 1000.0,
            "timestamp": pd.Timestamp("2026-11-01 10:00:00"),
            "transaction_type": "Transfer",
            "is_synthetic_suspicious": "No",
            "source": "synthetic"
        },
        {
            "transaction_id": "TX_CYC_2",
            "case_id": "CASE_CYC",
            "sender_bank": "Bank Beta",
            "receiver_bank": "Bank Gamma",
            "sender_account": "CYC_B",
            "receiver_account": "CYC_C",
            "amount": 950.0,
            "timestamp": pd.Timestamp("2026-11-01 10:10:00"),
            "transaction_type": "Transfer",
            "is_synthetic_suspicious": "No",
            "source": "synthetic"
        },
        {
            "transaction_id": "TX_CYC_3",
            "case_id": "CASE_CYC",
            "sender_bank": "Bank Gamma",
            "receiver_bank": "Bank Alpha",
            "sender_account": "CYC_C",
            "receiver_account": "CYC_A",
            "amount": 900.0,
            "timestamp": pd.Timestamp("2026-11-01 10:20:00"),
            "transaction_type": "Transfer",
            "is_synthetic_suspicious": "No",
            "source": "synthetic"
        }
    ])
    feats = case_features(cycle_df)
    assert len(feats) == len(FEATURES)
    for k, v in feats.items():
        assert not np.isnan(v), f"Feature {k} is NaN"
        assert not np.isinf(v), f"Feature {k} is infinite"
    assert feats["hop_depth"] >= 1
