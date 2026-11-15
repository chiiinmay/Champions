"""Generates SYNTHETIC multi-bank transactions with known ground truth.
Run:  python dataset/data_generator.py
"""
import random
from datetime import datetime, timedelta
from itertools import combinations
from pathlib import Path

import numpy as np
import pandas as pd

SEED = 42
random.seed(SEED)
np.random.seed(SEED)

OUT = Path(__file__).parent
BANKS = ["Bank Alpha", "Bank Beta", "Bank Gamma"]
PREFIX = {"Bank Alpha": "A", "Bank Beta": "B", "Bank Gamma": "G"}
T0 = datetime(2026, 11, 1, 9, 0, 0)

ACCT_BANK = {}
_rows = []
_counter = [0]


def acct(bank, label):
    a = f"{PREFIX[bank]}{label}"
    ACCT_BANK[a] = bank
    return a


def tx(case_id, s, r, amount, ts, ttype="Transfer", suspicious="No", source="synthetic"):
    _counter[0] += 1
    _rows.append(dict(
        transaction_id=f"TX{_counter[0]:05d}", case_id=case_id,
        sender_bank=ACCT_BANK[s], receiver_bank=ACCT_BANK[r],
        sender_account=s, receiver_account=r, amount=round(amount, 2),
        timestamp=ts.strftime("%Y-%m-%d %H:%M:%S"), transaction_type=ttype,
        is_synthetic_suspicious=suspicious, source=source))


def layered_case(case_id, start, victims, amounts, mule1, layer2, cashout,
                 speed=1.0, pass_pct=0.97):
    """Pattern P1. `speed` multiplies all time gaps (1.0 = rapid, 40 = slow)."""
    t = start
    total = 0.0
    for v, a in zip(victims, amounts):
        tx(case_id, v, mule1, a, t, suspicious="Yes")
        total += a
        t += timedelta(minutes=random.uniform(5, 20) * speed)
    t += timedelta(minutes=random.uniform(10, 25) * speed)
    share = total * 0.95 / len(layer2)
    forwarded = []
    for m in layer2:
        amt = share * random.uniform(0.95, 1.05)
        tx(case_id, mule1, m, amt, t, suspicious="Yes")
        forwarded.append((m, amt, t))
        t += timedelta(minutes=random.uniform(3, 10) * speed)
    for m, amt, tt in forwarded:
        t2 = tt + timedelta(minutes=random.uniform(15, 40) * speed)
        tx(case_id, m, cashout, amt * pass_pct, t2, suspicious="Yes")


def build():
    A, B, G = BANKS
    # shared / fixed accounts
    Z = acct(B, "900")          # shared intermediary
    G777 = acct(G, "777")       # repeated beneficiary (A and B)
    G888 = acct(G, "888")
    U001 = acct(A, "U001")      # popular hub account

    # ---- CASE_A, CASE_B, CASE_C: connected through Z -------------------
    layered_case("CASE_A", T0 + timedelta(days=0),
                 [acct(A, "101"), acct(A, "102")], [20000, 35000],
                 Z, [acct(G, "210"), acct(G, "211"), acct(A, "220")], G777)
    # hub-trap payment inside CASE_A
    tx("CASE_A", G777, U001, 1500, T0 + timedelta(days=0, hours=4), suspicious="Yes")

    layered_case("CASE_B", T0 + timedelta(days=3),
                 [acct(B, "301"), acct(B, "302"), acct(B, "303")], [15000, 25000, 18000],
                 Z, [acct(A, "410"), acct(A, "411"), acct(B, "420")], G777)

    layered_case("CASE_C", T0 + timedelta(days=6),
                 [acct(G, "501"), acct(G, "502")], [40000, 22000],
                 Z, [acct(A, "610"), acct(B, "611"), acct(G, "612")], G888)

    # ---- CASE_D: no shared accounts, same behaviour (Missing Link) -----
    layered_case("CASE_D", T0 + timedelta(days=9),
                 [acct(A, "701"), acct(G, "701")], [30000, 28000],
                 acct(B, "950"), [acct(A, "810"), acct(G, "811"), acct(B, "812")],
                 acct(A, "999"))

    # ---- CASE_E: control (single large slow transfer) ------------------
    v, m, o = acct(A, "901"), acct(B, "960"), acct(G, "960")
    tx("CASE_E", v, m, 120000, T0 + timedelta(days=11), suspicious="Yes")
    tx("CASE_E", m, o, 118000, T0 + timedelta(days=13, hours=2), suspicious="Yes")

    # ---- CASE_F: near-miss (slow, 2 layer-2 accounts, hub cash-out) ----
    layered_case("CASE_F", T0 + timedelta(days=14),
                 [acct(B, "801")], [26000],
                 acct(B, "970"), [acct(A, "971"), acct(G, "972")], U001,
                 speed=40)

    # ---- NORM_00..39: small normal clusters ----------------------------
    for i in range(40):
        cid = f"NORM_{i:02d}"
        n_acc = random.randint(3, 5)
        accs = [acct(random.choice(BANKS), f"N{i:02d}{j}") for j in range(n_acc)]
        t = T0 + timedelta(days=random.uniform(0, 20), hours=random.uniform(0, 12))
        for _ in range(random.randint(2, 5)):
            s, r = random.sample(accs, 2)
            amt = float(np.random.lognormal(mean=np.log(3000), sigma=0.8))
            tx(cid, s, r, amt, t, ttype=random.choice(["Transfer", "Payment"]))
            t += timedelta(hours=random.uniform(3, 60))

    # ---- BACKGROUND: ordinary traffic + hub ----------------------------
    bg = [acct(random.choice(BANKS), f"BG{j:03d}") for j in range(150)]
    for _ in range(400):
        s, r = random.sample(bg, 2)
        t = T0 + timedelta(days=random.uniform(0, 20), minutes=random.uniform(0, 1440))
        tx("BACKGROUND", s, r, float(np.random.lognormal(np.log(2500), 0.9)), t)
    for s in random.sample(bg, 40):
        t = T0 + timedelta(days=random.uniform(0, 20), minutes=random.uniform(0, 1440))
        tx("BACKGROUND", s, U001, float(np.random.lognormal(np.log(1200), 0.5)), t,
           ttype="Bill Payment")

    df = pd.DataFrame(_rows).sort_values("timestamp").reset_index(drop=True)
    df.to_csv(OUT / "transactions.csv", index=False)

    # cases.csv
    df["timestamp"] = pd.to_datetime(df["timestamp"])
    c = (df[df.case_id != "BACKGROUND"].groupby("case_id")
         .agg(n_transactions=("transaction_id", "count"),
              start_time=("timestamp", "min"), end_time=("timestamp", "max"))
         .reset_index())
    c["case_type"] = np.where(c.case_id.str.startswith("CASE_"),
                              "reported_fraud", "normal_cluster")
    c[["case_id", "case_type", "n_transactions", "start_time", "end_time"]] \
        .to_csv(OUT / "cases.csv", index=False)

    # ground_truth.csv  (one row per pair of reported cases)
    reported = ["CASE_A", "CASE_B", "CASE_C", "CASE_D", "CASE_E", "CASE_F"]
    connected = {("CASE_A", "CASE_B"), ("CASE_A", "CASE_C"), ("CASE_B", "CASE_C")}
    similar = connected | {("CASE_A", "CASE_D"), ("CASE_B", "CASE_D"), ("CASE_C", "CASE_D")}
    rows = []
    for a, b in combinations(reported, 2):
        key = (a, b)
        if key in connected:
            rel, note = "shared_account", "share intermediary B900 (and G777 for A-B)"
        elif "CASE_D" in key and (set(key) - {"CASE_D"}) <= {"CASE_A", "CASE_B", "CASE_C"}:
            rel, note = "similar_pattern", "same behaviour, no common accounts"
        elif "CASE_F" in key and "CASE_A" in key:
            rel, note = "hub_only", "both touch popular hub U001; should be ignored"
        elif "CASE_F" in key:
            rel, note = "near_miss", "layered but slow; timing differs"
        else:
            rel, note = "unrelated", "control case"
        rows.append(dict(case_1=a, case_2=b, relation=rel,
                         expect_connected="Yes" if key in connected else "No",
                         expect_similar="Yes" if key in similar else "No", notes=note))
    pd.DataFrame(rows).to_csv(OUT / "ground_truth.csv", index=False)
    print(f"transactions={len(df)}  cases={len(c)}  ground_truth_pairs={len(rows)}")


if __name__ == "__main__":
    build()
