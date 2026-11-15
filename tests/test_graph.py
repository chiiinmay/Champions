from backend.graph_engine import load_transactions
from backend.cross_case_detection import discover_connections
from backend.money_flow import money_trail

df = load_transactions("dataset/transactions.csv")


def test_shared_intermediary_found():
    out = discover_connections(df)
    pairs = {(c["case_a"], c["case_b"]) for c in out["connections"]}
    assert {("CASE_A", "CASE_B"), ("CASE_A", "CASE_C"), ("CASE_B", "CASE_C")} <= pairs


def test_hub_ignored():
    out = discover_connections(df)
    assert any(h["account"] == "AU001" for h in out["ignored_hub_accounts"])
    pairs = {(c["case_a"], c["case_b"]) for c in out["connections"]}
    assert ("CASE_A", "CASE_F") not in pairs


def test_case_d_not_connected_by_accounts():
    out = discover_connections(df)
    assert all("CASE_D" not in (c["case_a"], c["case_b"]) for c in out["connections"])


def test_split_detected():
    r = money_trail(df[df.case_id == "CASE_A"])
    assert len(r["splits"]) >= 1 and len(r["paths"]) >= 1
