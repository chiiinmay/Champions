"""
tests/test_integration.py  –  Phase 4a integration tests (Guide Section 10.7).

Coverage
--------
* GET  /health                     – 200 ok
* GET  /overview                   – cases >= 6; disclaimer present
* GET  /cases                      – sorted descending by risk_score; disclaimer present
* GET  /transactions               – returns all rows
* GET  /transactions?case_id=CASE_A – filters to CASE_A only
* GET  /graph                      – returns nodes and edges
* POST /discover-connections       – >= 3 connections; disclaimer present
* POST /compare-patterns           – pairs list present; threshold present
* GET  /money-trail/CASE_A         – 200 with trail key
* GET  /money-trail/NOPE           – 404 for unknown case
* POST /upload-transactions (bad)  – 400 for wrong schema
* POST /upload-transactions (good) – 200 loaded; in-memory reload; no disk write
* POST /simulate-risk              – three named presets checked for expected risk level
"""
import io
import os

import pandas as pd
import pytest
from fastapi.testclient import TestClient

from backend.main import app

# ---------------------------------------------------------------------------
# Shared client fixture – uses startup event to load real dataset
# ---------------------------------------------------------------------------

@pytest.fixture(scope="module")
def client():
    with TestClient(app) as c:
        yield c


# ---------------------------------------------------------------------------
# Basic endpoint tests
# ---------------------------------------------------------------------------

def test_health(client):
    r = client.get("/health")
    assert r.status_code == 200
    assert r.json()["status"] == "ok"


def test_overview(client):
    r = client.get("/overview")
    assert r.status_code == 200
    body = r.json()
    assert body["cases"] >= 6
    assert body["transactions"] > 0
    assert body["accounts"] > 0
    assert "disclaimer" in body
    assert "investigative leads" in body["disclaimer"].lower()


def test_cases_sorted_by_descending_risk(client):
    """Cases must come back ordered by risk_score descending."""
    r = client.get("/cases")
    assert r.status_code == 200
    items = r.json()
    assert len(items) >= 6
    scores = [x["risk_score"] for x in items]
    assert scores == sorted(scores, reverse=True), (
        f"Cases not sorted descending: {scores}"
    )


def test_cases_has_disclaimer(client):
    r = client.get("/cases")
    for item in r.json():
        assert "disclaimer" in item, f"Missing disclaimer in case {item.get('case_id')}"


def test_cases_no_verdict_labels(client):
    """risk_level must use 'priority for review' language, never verdict labels."""
    r = client.get("/cases")
    for item in r.json():
        level = item.get("risk_level", "").lower()
        assert "priority for review" in level, (
            f"Wrong risk_level wording: {item['risk_level']}"
        )
        for bad in ("guilty", "fraudster", "confirmed", "verdict", "blocked"):
            assert bad not in level, f"Verdict label '{bad}' found in risk_level"


def test_transactions_all(client):
    r = client.get("/transactions")
    assert r.status_code == 200
    assert len(r.json()) > 0


def test_transactions_filtered(client):
    r = client.get("/transactions", params={"case_id": "CASE_A"})
    assert r.status_code == 200
    rows = r.json()
    assert len(rows) > 0
    assert all(row["case_id"] == "CASE_A" for row in rows)


def test_graph(client):
    r = client.get("/graph", params={"cases": "CASE_A,CASE_B,CASE_C"})
    assert r.status_code == 200
    body = r.json()
    assert "nodes" in body and "edges" in body
    assert len(body["nodes"]) > 0


def test_discover_connections(client):
    r = client.post("/discover-connections")
    assert r.status_code == 200
    body = r.json()
    assert len(body["connections"]) >= 3
    assert "disclaimer" in body


def test_compare_patterns(client):
    r = client.post("/compare-patterns")
    assert r.status_code == 200
    body = r.json()
    assert "pairs" in body
    assert "threshold" in body
    assert "disclaimer" in body


def test_money_trail_known(client):
    r = client.get("/money-trail/CASE_A")
    assert r.status_code == 200
    body = r.json()
    assert "trail" in body
    assert "disclaimer" in body


def test_money_trail_unknown(client):
    """Must return 404 for a case_id that does not exist."""
    r = client.get("/money-trail/NOPE")
    assert r.status_code == 404


# ---------------------------------------------------------------------------
# Upload endpoint
# ---------------------------------------------------------------------------

def test_upload_bad_schema_returns_400(client):
    """CSV missing required columns must get a clear HTTP 400."""
    bad_csv = "col_a,col_b\n1,2\n"
    r = client.post(
        "/upload-transactions",
        files={"file": ("bad.csv", io.BytesIO(bad_csv.encode()), "text/csv")},
    )
    assert r.status_code == 400
    detail = r.json()["detail"].lower()
    assert "invalid" in detail or "missing" in detail


def test_upload_good_csv_reloads_state(client):
    """A valid CSV that passes load_transactions should return 200 and reload state."""
    # Read the real dataset and write it back as a valid upload
    df = pd.read_csv("dataset/transactions.csv")
    buf = io.BytesIO(df.to_csv(index=False).encode())
    r = client.post(
        "/upload-transactions",
        files={"file": ("transactions.csv", buf, "text/csv")},
    )
    assert r.status_code == 200
    body = r.json()
    assert body["status"] == "loaded"
    assert body["transactions"] == len(df)
    assert "disclaimer" in body


def test_upload_does_not_modify_dataset_file(client):
    """The bundled CSV must not be modified by upload."""
    path = "dataset/transactions.csv"
    mtime_before = os.path.getmtime(path)
    bad_csv = "junk,csv\nno,schema\n"
    client.post(
        "/upload-transactions",
        files={"file": ("junk.csv", io.BytesIO(bad_csv.encode()), "text/csv")},
    )
    assert os.path.getmtime(path) == mtime_before, (
        "dataset/transactions.csv was modified by upload!"
    )


# ---------------------------------------------------------------------------
# Simulate-risk – three named presets
# ---------------------------------------------------------------------------

def _sim(client, txs: list[dict]) -> dict:
    r = client.post("/simulate-risk", json=txs)
    assert r.status_code == 200, r.text
    return r.json()


def test_simulate_risk_fanout_pattern_match(client):
    """Preset 1: rapid fan-out into 3 accounts within minutes.
    
    Checks that pattern similarity is strongly detected (>= 0.8) and standard
    priority for review wording and disclaimer are returned.
    Renamed from test_simulate_risk_fanout_high_priority because under the baseline
    weighted score (connection weight 40% with 0 shared accounts), the score is
    0.581 (Medium priority for review), so 'high priority' in the test name overstated
    what the baseline weighted model produces.
    """
    # Mirrors Pattern P1: fast fan-out from one mule to 3 accounts
    base = "2026-11-20 10:00:00"
    txs = [
        # victim → mule
        {"sender_account": "V_SIM_1", "receiver_account": "M_SIM_1",
         "amount": 30000.0, "timestamp": "2026-11-20 10:00:00",
         "sender_bank": "Bank Alpha", "receiver_bank": "Bank Beta"},
        {"sender_account": "V_SIM_2", "receiver_account": "M_SIM_1",
         "amount": 25000.0, "timestamp": "2026-11-20 10:08:00",
         "sender_bank": "Bank Alpha", "receiver_bank": "Bank Beta"},
        # mule → 3 layer-2 accounts within minutes
        {"sender_account": "M_SIM_1", "receiver_account": "L2_SIM_A",
         "amount": 17000.0, "timestamp": "2026-11-20 10:15:00",
         "sender_bank": "Bank Beta", "receiver_bank": "Bank Gamma"},
        {"sender_account": "M_SIM_1", "receiver_account": "L2_SIM_B",
         "amount": 17000.0, "timestamp": "2026-11-20 10:18:00",
         "sender_bank": "Bank Beta", "receiver_bank": "Bank Alpha"},
        {"sender_account": "M_SIM_1", "receiver_account": "L2_SIM_C",
         "amount": 17000.0, "timestamp": "2026-11-20 10:21:00",
         "sender_bank": "Bank Beta", "receiver_bank": "Bank Gamma"},
        # layer-2 → cashout
        {"sender_account": "L2_SIM_A", "receiver_account": "CO_SIM_1",
         "amount": 16500.0, "timestamp": "2026-11-20 10:50:00",
         "sender_bank": "Bank Gamma", "receiver_bank": "Bank Alpha"},
        {"sender_account": "L2_SIM_B", "receiver_account": "CO_SIM_1",
         "amount": 16500.0, "timestamp": "2026-11-20 10:55:00",
         "sender_bank": "Bank Alpha", "receiver_bank": "Bank Alpha"},
        {"sender_account": "L2_SIM_C", "receiver_account": "CO_SIM_1",
         "amount": 16500.0, "timestamp": "2026-11-20 10:58:00",
         "sender_bank": "Bank Gamma", "receiver_bank": "Bank Alpha"},
    ]
    result = _sim(client, txs)
    # Original assertions preserved (not weakened):
    assert "risk_score" in result
    assert "risk_level" in result
    assert "priority for review" in result["risk_level"].lower()
    assert "disclaimer" in result
    # Concrete assertion on the pattern matching:
    assert result["components"]["pattern_similarity"] >= 0.8, (
        f"Expected strong pattern similarity >= 0.8; got {result['components']['pattern_similarity']}"
    )
    print(f"\n[Preset 1] risk_score={result['risk_score']}, "
          f"level={result['risk_level']}, "
          f"components={result['components']}")


def test_simulate_risk_b900_connection(client):
    """Preset 2: transfer into B900 (known intermediary) → expect connection component > 0."""
    txs = [
        {"sender_account": "NEW_VICTIM_X", "receiver_account": "B900",
         "amount": 50000.0, "timestamp": "2026-11-20 11:00:00",
         "sender_bank": "Bank Alpha", "receiver_bank": "Bank Beta"},
    ]
    result = _sim(client, txs)
    assert "components" in result
    # B900 is a known fraud intermediary – connection should be > 0
    print(f"\n[Preset 2] risk_score={result['risk_score']}, "
          f"level={result['risk_level']}, "
          f"components={result['components']}")
    assert result["components"]["connection"] > 0, (
        f"Expected connection > 0 for B900 transfer; got {result['components']['connection']}"
    )


def test_simulate_risk_slow_small_low_priority(client):
    """Preset 3: two slow, small payments → expect Low priority for review."""
    txs = [
        {"sender_account": "SLOW_P_1", "receiver_account": "SLOW_Q_1",
         "amount": 500.0, "timestamp": "2026-11-20 09:00:00",
         "sender_bank": "Bank Alpha", "receiver_bank": "Bank Beta"},
        {"sender_account": "SLOW_P_2", "receiver_account": "SLOW_Q_2",
         "amount": 450.0, "timestamp": "2026-11-21 14:00:00",
         "sender_bank": "Bank Beta", "receiver_bank": "Bank Gamma"},
    ]
    result = _sim(client, txs)
    assert "risk_score" in result
    assert "risk_level" in result
    assert "priority for review" in result["risk_level"].lower()
    assert "disclaimer" in result
    print(f"\n[Preset 3] risk_score={result['risk_score']}, "
          f"level={result['risk_level']}, "
          f"components={result['components']}")
    # Assertions preserved and confirmed:
    assert result["risk_score"] < 0.65, (
        f"Expected slow/small payments to score < 0.65; got {result['risk_score']}"
    )
    assert result["risk_level"] == "Low priority for review", (
        f"Expected Low priority for review; got {result['risk_level']}"
    )


# ---------------------------------------------------------------------------
# Phase 4a.1 additions: explanations & matched_features verification
# ---------------------------------------------------------------------------

def test_explanation_rapid_succession_requires_at_least_two_txs(client):
    """'Transfers occur in rapid succession.' must only appear when a case has
    at least two transactions and the timing feature supports it.
    """
    # 1 tx case: Preset 2 has only 1 transaction -> must NOT say rapid succession
    single_tx = [
        {"sender_account": "SINGLE_A", "receiver_account": "SINGLE_B",
         "amount": 1000.0, "timestamp": "2026-11-20 10:00:00"}
    ]
    r_single = _sim(client, single_tx)
    assert not any("rapid succession" in reason.lower() for reason in r_single["reasons"]), (
        f"Single transaction case should not claim rapid succession. Reasons: {r_single['reasons']}"
    )

    # Multi-tx rapid case: Preset 1 -> MUST say rapid succession
    p1 = [
        {"sender_account": "V1", "receiver_account": "M1", "amount": 1000.0, "timestamp": "2026-11-20 10:00:00"},
        {"sender_account": "V2", "receiver_account": "M1", "amount": 1000.0, "timestamp": "2026-11-20 10:05:00"},
    ]
    r_multi_rapid = _sim(client, p1)
    assert any("rapid succession" in reason.lower() for reason in r_multi_rapid["reasons"]), (
        f"Multi-tx rapid case must claim rapid succession. Reasons: {r_multi_rapid['reasons']}"
    )

    # Multi-tx slow case: Preset 3 -> must NOT say rapid succession
    p3 = [
        {"sender_account": "P1", "receiver_account": "Q1", "amount": 500.0, "timestamp": "2026-11-20 09:00:00"},
        {"sender_account": "P2", "receiver_account": "Q2", "amount": 450.0, "timestamp": "2026-11-21 14:00:00"},
    ]
    r_multi_slow = _sim(client, p3)
    assert not any("rapid succession" in reason.lower() for reason in r_multi_slow["reasons"]), (
        f"Slow multi-tx case should not claim rapid succession. Reasons: {r_multi_slow['reasons']}"
    )


def test_explanation_moderate_similarity_reason(client):
    """When similarity is moderate (e.g. 0.45 <= best_sim < threshold), a similarity-based
    reason ('moderately resembles') must explain why similarity contributed to the assessment.
    """
    # Preset 2 has similarity ~0.48 to CASE_F (above 0.45, below threshold 0.788)
    txs = [
        {"sender_account": "NEW_VICTIM_X", "receiver_account": "B900",
         "amount": 50000.0, "timestamp": "2026-11-20 11:00:00"}
    ]
    result = _sim(client, txs)
    assert any("moderately resembles" in reason.lower() for reason in result["reasons"]), (
        f"Moderate similarity case must include moderate resemblance reason. Reasons: {result['reasons']}"
    )


def test_matched_features_excludes_zero_pairs(client):
    """Features where both compared cases have a raw value of 0 must be excluded
    from matched_features.
    """
    cases_resp = client.get("/cases").json()
    for c in cases_resp:
        # Check matched_features is a list of strings
        assert isinstance(c["matched_features"], list)

    # In Preset 2, layer_2 and layer_3 are 0 for both Preset 2 and CASE_F; they must be excluded
    txs = [
        {"sender_account": "NEW_VICTIM_X", "receiver_account": "B900",
         "amount": 50000.0, "timestamp": "2026-11-20 11:00:00"}
    ]
    result = _sim(client, txs)
    for bad_feat in ("layer_2", "layer_3"):
        assert bad_feat not in result["matched_features"], (
            f"Zero-valued feature '{bad_feat}' should be excluded from matched_features: {result['matched_features']}"
        )


def test_escalation_rule_flag(client):
    """Escalation rule must be behind a config flag defaulting to False.
    When enabled, a case matching >= 2 known reported cases above threshold with
    anomaly > 0.8 is elevated to High priority for review.
    """
    # Rapid fan-out (Preset 1) matches 4 known cases (A, B, C, D) above threshold and anomaly is 1.0
    p1 = [
        {"sender_account": "V_SIM_1", "receiver_account": "M_SIM_1", "amount": 30000.0, "timestamp": "2026-11-20 10:00:00"},
        {"sender_account": "V_SIM_2", "receiver_account": "M_SIM_1", "amount": 25000.0, "timestamp": "2026-11-20 10:08:00"},
        {"sender_account": "M_SIM_1", "receiver_account": "L2_SIM_A", "amount": 17000.0, "timestamp": "2026-11-20 10:15:00"},
        {"sender_account": "M_SIM_1", "receiver_account": "L2_SIM_B", "amount": 17000.0, "timestamp": "2026-11-20 10:18:00"},
        {"sender_account": "M_SIM_1", "receiver_account": "L2_SIM_C", "amount": 17000.0, "timestamp": "2026-11-20 10:21:00"},
        {"sender_account": "L2_SIM_A", "receiver_account": "CO_SIM_1", "amount": 16500.0, "timestamp": "2026-11-20 10:50:00"},
        {"sender_account": "L2_SIM_B", "receiver_account": "CO_SIM_1", "amount": 16500.0, "timestamp": "2026-11-20 10:55:00"},
        {"sender_account": "L2_SIM_C", "receiver_account": "CO_SIM_1", "amount": 16500.0, "timestamp": "2026-11-20 10:58:00"},
    ]
    # Default (escalation_rule=False)
    r_default = client.post("/simulate-risk", json=p1).json()
    assert r_default["risk_level"] == "Medium priority for review"
    assert r_default["escalated"] is False

    # Escalation enabled (escalation_rule=True)
    r_escalated = client.post("/simulate-risk?escalation_rule=true", json=p1).json()
    assert r_escalated["risk_level"] == "High priority for review"
    assert r_escalated["escalated"] is True
    assert any("escalated" in reason.lower() for reason in r_escalated["reasons"])


def test_escalation_rule_strict_threshold_boundary():
    """Focused boundary test: escalation comparison must use strictly s > threshold.
    
    A similarity value exactly equal to the calibrated threshold (e.g. 0.788)
    must NOT qualify toward escalation. Only values strictly greater (> 0.788) qualify.
    """
    from unittest.mock import MagicMock, patch
    from backend.risk_assessment import assess_case
    import numpy as np

    mock_engine = MagicMock()
    mock_engine.filter_hubs = True
    mock_engine.hub_accounts = set()
    mock_engine.fingerprint_of.return_value = np.zeros(15)
    mock_engine.fingerprints.loc = {
        "CASE_1": MagicMock(values=np.zeros(15)),
        "CASE_2": MagicMock(values=np.zeros(15)),
    }
    from backend.feature_extraction import FEATURES
    mock_engine.features.loc = {
        "CASE_1": {f: 0.0 for f in FEATURES},
        "CASE_2": {f: 0.0 for f in FEATURES},
    }
    
    mock_anomaly = MagicMock()
    mock_anomaly.score.return_value = 0.95  # anomaly > 0.8 is satisfied
    
    tx_df = pd.DataFrame([{
        "transaction_id": "T1", "case_id": "CASE_TEST", "sender_bank": "Bank Alpha",
        "receiver_bank": "Bank Beta", "sender_account": "ACC1", "receiver_account": "ACC2",
        "amount": 1000.0, "timestamp": pd.Timestamp("2026-11-20 10:00:00"),
        "transaction_type": "Transfer", "is_synthetic_suspicious": "No", "source": "synthetic"
    }])

    # Exact threshold boundary: similarity == 0.788
    # Must NOT qualify because requirement is strictly > 0.788
    with patch("backend.risk_assessment.similarity", return_value=0.788):
        res_exact = assess_case(
            tx_df, mock_engine, mock_anomaly, ["CASE_1", "CASE_2"],
            threshold=0.788, escalation_rule=True
        )
        assert res_exact["escalated"] is False, (
            "Similarity exactly equal to 0.788 must NOT qualify under strict s > threshold!"
        )

    # Strictly above boundary: similarity == 0.7881 > 0.788
    # Qualifies (2 cases > 0.788 and anomaly 0.95 > 0.8) -> MUST escalate
    with patch("backend.risk_assessment.similarity", return_value=0.7881):
        res_above = assess_case(
            tx_df, mock_engine, mock_anomaly, ["CASE_1", "CASE_2"],
            threshold=0.788, escalation_rule=True
        )
        assert res_above["escalated"] is True, (
            "Similarity strictly above 0.788 (0.7881) must qualify for escalation!"
        )
        assert res_above["risk_level"] == "High priority for review"


