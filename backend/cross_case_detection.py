from itertools import combinations
import networkx as nx
import pandas as pd

HUB_DEGREE_THRESHOLD = 25   # Accounts with total degree > 25 across all transactions are treated as hubs


def _account_cases(reported: pd.DataFrame) -> pd.DataFrame:
    s = reported[["case_id", "transaction_id", "sender_account"]].rename(
        columns={"sender_account": "account"}).assign(direction="out")
    r = reported[["case_id", "transaction_id", "receiver_account"]].rename(
        columns={"receiver_account": "account"}).assign(direction="in")
    return pd.concat([s, r], ignore_index=True)


def _role(sub: pd.DataFrame) -> str:
    dirs = set(sub.direction)
    if dirs == {"in", "out"}:
        return "intermediary"
    return "beneficiary" if dirs == {"in"} else "source"


def discover_connections(df: pd.DataFrame, hub_threshold: int = HUB_DEGREE_THRESHOLD) -> dict:
    """Discovers shared accounts across reported fraud cases while filtering high-degree hub accounts.
    
    Includes supporting transaction IDs as concrete evidence for every detected cross-case link.
    """
    reported = df[df.case_id.str.startswith("CASE_")]
    total_deg = pd.concat([df.sender_account, df.receiver_account]).value_counts()
    ac = _account_cases(reported)

    bank_of = {}
    for r in df.itertuples():
        bank_of[r.sender_account] = r.sender_bank
        bank_of[r.receiver_account] = r.receiver_bank

    ignored = []
    shared_by_account = {}

    for account, sub in ac.groupby("account"):
        cases = sorted(sub.case_id.unique())
        if len(cases) < 2:
            continue
        if total_deg[account] > hub_threshold:
            ignored.append({"account": account, "total_degree": int(total_deg[account])})
            continue
        shared_by_account[account] = {
            "cases": cases,
            "df": sub,
            "role": _role(sub)
        }

    connections = {}
    for account, info in shared_by_account.items():
        for a, b in combinations(info["cases"], 2):
            c = connections.setdefault((a, b), {"shared_accounts": [], "supporting": set()})
            c["shared_accounts"].append({
                "account": account,
                "role": info["role"],
                "bank": bank_of.get(account, "Unknown")
            })
            sub = info["df"]
            c["supporting"] |= set(sub[sub.case_id.isin([a, b])].transaction_id)

    out = []
    for (a, b), c in sorted(connections.items()):
        names = ", ".join(f"{x['account']} ({x['role']})" for x in c["shared_accounts"])
        out.append({
            "case_a": a,
            "case_b": b,
            "shared_accounts": c["shared_accounts"],
            "supporting_transactions": sorted(c["supporting"]),
            "explanation": f"{a} and {b} both involve {names}."
        })

    H = nx.Graph()
    H.add_nodes_from(reported.case_id.unique())
    H.add_edges_from((c["case_a"], c["case_b"]) for c in out)
    groups = [sorted(g) for g in nx.connected_components(H) if len(g) > 1]

    return {
        "connections": out,
        "case_groups": groups,
        "ignored_hub_accounts": ignored
    }


def repeated_beneficiaries(connections_result: dict) -> list[dict]:
    """Helper for UI to extract unique shared accounts acting as beneficiaries."""
    seen = set()
    result = []
    for c in connections_result.get("connections", []):
        for acct in c.get("shared_accounts", []):
            if acct["role"] == "beneficiary" and acct["account"] not in seen:
                seen.add(acct["account"])
                result.append(acct)
    return result


def common_intermediaries(connections_result: dict) -> list[dict]:
    """Helper for UI to extract unique shared accounts acting as intermediaries."""
    seen = set()
    result = []
    for c in connections_result.get("connections", []):
        for acct in c.get("shared_accounts", []):
            if acct["role"] == "intermediary" and acct["account"] not in seen:
                seen.add(acct["account"])
                result.append(acct)
    return result
