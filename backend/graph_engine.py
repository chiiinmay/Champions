import networkx as nx
import pandas as pd

REQUIRED = [
    "transaction_id", "case_id", "sender_bank", "receiver_bank",
    "sender_account", "receiver_account", "amount", "timestamp",
    "transaction_type", "is_synthetic_suspicious", "source"
]


def load_transactions(path_or_buffer) -> pd.DataFrame:
    """Core data-loading function with validation according to the frozen data contract."""
    df = pd.read_csv(path_or_buffer)
    missing = [c for c in REQUIRED if c not in df.columns]
    if missing:
        raise ValueError(f"Missing columns: {missing}")
    df["timestamp"] = pd.to_datetime(df["timestamp"])
    df["amount"] = df["amount"].astype(float)
    if (df["amount"] <= 0).any():
        raise ValueError("amount must be positive")
    if df["transaction_id"].duplicated().any():
        raise ValueError("duplicate transaction_id")
    return df.sort_values("timestamp").reset_index(drop=True)


def build_graph(df: pd.DataFrame, cases=None) -> nx.MultiDiGraph:
    """Constructs a directed multi-graph where accounts = nodes and transactions = directed edges."""
    d = df if cases is None else df[df.case_id.isin(cases)]
    G = nx.MultiDiGraph()
    for r in d.itertuples(index=False):
        G.add_node(r.sender_account, bank=r.sender_bank)
        G.add_node(r.receiver_account, bank=r.receiver_bank)
        G.add_edge(
            r.sender_account,
            r.receiver_account,
            key=r.transaction_id,
            transaction_id=r.transaction_id,
            amount=float(r.amount),
            timestamp=r.timestamp,
            case_id=r.case_id,
            transaction_type=r.transaction_type
        )
    return G


def graph_to_cytoscape(G: nx.MultiDiGraph, highlight_accounts=()) -> dict:
    """Converts a NetworkX MultiDiGraph to Cytoscape.js compatible JSON format."""
    hl = set(highlight_accounts)
    nodes = [
        {
            "data": {
                "id": n,
                "label": n,
                "bank": a.get("bank", ""),
                "shared": n in hl
            }
        }
        for n, a in G.nodes(data=True)
    ]
    edges = [
        {
            "data": {
                "id": k,
                "source": u,
                "target": v,
                "label": f"₹{d['amount']:,.0f}",
                "case_id": d["case_id"],
                "timestamp": d["timestamp"].strftime("%Y-%m-%d %H:%M:%S")
            }
        }
        for u, v, k, d in G.edges(keys=True, data=True)
    ]
    return {"nodes": nodes, "edges": edges}
