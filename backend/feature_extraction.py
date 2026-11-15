import networkx as nx
import numpy as np
import pandas as pd

FEATURES = [
    "log_avg_amount", "n_tx", "log_median_gap_min", "log_duration_min",
    "split_ratio", "n_beneficiaries", "in_out_ratio", "n_passthrough",
    "hop_depth", "retention", "consolidation_ratio",
    "layer_0", "layer_1", "layer_2", "layer_3"
]


def case_features(c: pd.DataFrame, hub_accounts: set = None) -> dict:
    """Extracts 15 structural and dynamic features from a case's transactions.
    
    If hub_accounts is provided, transactions involving these high-degree infrastructure
    accounts are filtered out prior to feature extraction to prevent incidental utility
    payments from distorting the underlying money-laundering topology.
    """
    if hub_accounts:
        c = c[~c.sender_account.isin(hub_accounts) & ~c.receiver_account.isin(hub_accounts)]

    c = c.sort_values("timestamp")
    n = len(c)
    if n == 0:
        return {f: 0.0 for f in FEATURES}

    senders = set(c.sender_account)
    receivers = set(c.receiver_account)
    passthrough = senders & receivers
    sources = senders - receivers
    terminals = receivers - senders

    gaps = c.timestamp.diff().dropna().dt.total_seconds() / 60
    median_gap = float(gaps.median()) if len(gaps) > 0 else 0.0
    duration = float((c.timestamp.max() - c.timestamp.min()).total_seconds() / 60) if n > 1 else 0.0

    # Hop depth via time-respecting or structural DAG
    G = nx.DiGraph()
    G.add_edges_from(zip(c.sender_account, c.receiver_account))
    try:
        depth = nx.dag_longest_path_length(G)
    except nx.NetworkXUnfeasible:
        # Graph contains cycles; fallback safely to node count minus 1
        depth = max(len(G.nodes) - 1, 0)

    # Layer profile: depth of each transaction's sender from a source
    level = {s: 0 for s in sources}
    if nx.is_directed_acyclic_graph(G):
        for u in nx.topological_sort(G):
            for v in G.successors(u):
                level[v] = max(level.get(v, 0), level.get(u, 0) + 1)
    layers = np.zeros(4)
    for s in c.sender_account:
        layers[min(level.get(s, 0), 3)] += 1
    layers = layers / max(n, 1)

    out_deg = c.groupby("sender_account").receiver_account.nunique()
    in_deg = c.groupby("receiver_account").sender_account.nunique()
    src_amt = float(c[c.sender_account.isin(sources)].amount.sum())
    term_amt = float(c[c.receiver_account.isin(terminals)].amount.sum())
    recv_pt = float(c[c.receiver_account.isin(passthrough)].amount.sum())
    send_pt = float(c[c.sender_account.isin(passthrough)].amount.sum())

    relevant_in = in_deg[in_deg.index.isin(passthrough | terminals)]
    consolidation = int(relevant_in.max()) if len(relevant_in) > 0 else 0

    avg_amt = float(c.amount.mean()) if n > 0 else 0.0

    feat = {
        "log_avg_amount": float(np.log1p(avg_amt)),
        "n_tx": n,
        "log_median_gap_min": float(np.log1p(median_gap)),
        "log_duration_min": float(np.log1p(duration)),
        "split_ratio": int(out_deg.max()) if len(out_deg) > 0 else 0,
        "n_beneficiaries": len(terminals),
        "in_out_ratio": float(term_amt / src_amt) if src_amt > 0 else 0.0,
        "n_passthrough": len(passthrough),
        "hop_depth": int(depth),
        "retention": float(send_pt / recv_pt) if recv_pt > 0 else 0.0,
        "consolidation_ratio": consolidation,
        **{f"layer_{i}": float(layers[i]) for i in range(4)},
    }

    # Ensure all values are finite and non-NaN
    for k, v in feat.items():
        if np.isnan(v) or np.isinf(v):
            feat[k] = 0.0

    return feat


def all_case_features(df: pd.DataFrame, filter_hubs: bool = True, hub_threshold: int = 25) -> pd.DataFrame:
    """Computes features for all cases in df (excluding BACKGROUND ambient traffic).
    
    hub_accounts are determined globally across df if filter_hubs is True.
    """
    hub_accounts = None
    if filter_hubs:
        total_deg = pd.concat([df.sender_account, df.receiver_account]).value_counts()
        hub_accounts = set(total_deg[total_deg > hub_threshold].index)

    rows = []
    for cid, g in df[~df.case_id.isin(["BACKGROUND"])].groupby("case_id"):
        rows.append({"case_id": cid, **case_features(g, hub_accounts=hub_accounts)})
    return pd.DataFrame(rows).set_index("case_id")[FEATURES]
