import networkx as nx
import pandas as pd


def chronological_trail(case_df: pd.DataFrame) -> list[dict]:
    """Generates an ordered list of transfers for a specific case."""
    d = case_df.sort_values("timestamp")
    return [
        {
            "transaction_id": r.transaction_id,
            "time": r.timestamp.isoformat(),
            "from": r.sender_account,
            "to": r.receiver_account,
            "amount": float(r.amount),
            "from_bank": r.sender_bank,
            "to_bank": r.receiver_bank
        }
        for r in d.itertuples()
    ]


def detect_splitting(case_df: pd.DataFrame, window_min=30, min_targets=3) -> list[dict]:
    """Detects rapid fan-out: a sender account that transfers to >= min_targets distinct receivers within window_min."""
    out = []
    for sender, g in case_df.sort_values("timestamp").groupby("sender_account"):
        g = g.reset_index(drop=True)
        for i in range(len(g)):
            w = g[(g.timestamp >= g.timestamp[i]) &
                  (g.timestamp <= g.timestamp[i] + pd.Timedelta(minutes=window_min))]
            if w.receiver_account.nunique() >= min_targets:
                out.append({
                    "account": sender,
                    "targets": sorted(w.receiver_account.unique()),
                    "total": float(w.amount.sum()),
                    "transaction_ids": list(w.transaction_id)
                })
                break
    return out


def detect_consolidation(case_df: pd.DataFrame, window_min=120, min_sources=3) -> list[dict]:
    """Detects rapid consolidation: a receiver account that gets transfers from >= min_sources distinct senders within window_min."""
    out = []
    for receiver, g in case_df.sort_values("timestamp").groupby("receiver_account"):
        g = g.reset_index(drop=True)
        for i in range(len(g)):
            w = g[(g.timestamp >= g.timestamp[i]) &
                  (g.timestamp <= g.timestamp[i] + pd.Timedelta(minutes=window_min))]
            if w.sender_account.nunique() >= min_sources:
                out.append({
                    "account": receiver,
                    "sources": sorted(w.sender_account.unique()),
                    "total": float(w.amount.sum()),
                    "transaction_ids": list(w.transaction_id)
                })
                break
    return out


def time_respecting_paths(case_df: pd.DataFrame, max_depth=6) -> list[dict]:
    """Reconstructs source-to-destination paths where every consecutive transfer happens chronologically after the previous."""
    d = case_df.sort_values("timestamp")
    outgoing = {}
    for r in d.itertuples():
        outgoing.setdefault(r.sender_account, []).append(r)
    sources = set(d.sender_account) - set(d.receiver_account)
    paths = []

    def dfs(account, last_time, trail):
        nxt = [e for e in outgoing.get(account, []) if e.timestamp >= last_time]
        if not nxt or len(trail) >= max_depth:
            if trail:
                paths.append(list(trail))
            return
        for e in nxt:
            trail.append(e)
            dfs(e.receiver_account, e.timestamp, trail)
            trail.pop()

    for s in sources:
        dfs(s, pd.Timestamp.min, [])

    return [
        {
            "accounts": [p[0].sender_account] + [e.receiver_account for e in p],
            "transaction_ids": [e.transaction_id for e in p],
            "amount_entering": float(p[0].amount),
            "amount_leaving": float(p[-1].amount),
            "duration_min": round((p[-1].timestamp - p[0].timestamp).total_seconds() / 60, 1)
        }
        for p in paths
    ]


def money_trail(case_df: pd.DataFrame) -> dict:
    """Full money flow reconstruction combining chronological trail, fan-out, consolidation, and paths."""
    return {
        "trail": chronological_trail(case_df),
        "splits": detect_splitting(case_df),
        "consolidations": detect_consolidation(case_df),
        "paths": time_respecting_paths(case_df)
    }
