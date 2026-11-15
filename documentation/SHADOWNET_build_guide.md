# SHADOWNET: Complete Build Guide (From Scratch)

**AI-Powered Cross-Case Financial Fraud Intelligence: Round 2 working prototype**

This guide merges (a) the Round 2 team plan and (b) every suggestion from the Round 1 alignment review into one build document. Follow it top to bottom. Every change made because of the review is tagged **[R1-FIX]** so you can see why it exists.

> **Authorship note.** The organiser prohibits AI-made PPTs/PDFs. This guide covers building, testing and collecting evidence. The final presentation must be written and assembled by your team from your own code, screenshots and measured results (Section 15 only tells you *what evidence to collect*).

---

## Table of contents

1. [Product definition and guardrails](#1-product-definition-and-guardrails)
2. [Changes integrated from the alignment review](#2-changes-integrated-from-the-alignment-review)
3. [Team roles and ownership](#3-team-roles-and-ownership)
4. [Environment setup](#4-environment-setup)
5. [Repository structure](#5-repository-structure)
6. [Data contract (agree on this first)](#6-data-contract-agree-on-this-first)
7. [Member 1: Data engineering](#7-member-1-data-engineering--dataset)
8. [Member 2: Graph intelligence and money flow](#8-member-2-graph-intelligence--money-flow)
9. [Member 3: Pattern fingerprinting and risk](#9-member-3-pattern-fingerprinting--risk-assessment)
10. [Member 4: Backend API, dashboard and integration](#10-member-4-backend-api-dashboard--integration)
11. [Schedule](#11-schedule-5-day-plan-with-3-day-and-2-day-cuts)
12. [Testing and evaluation](#12-testing-and-evaluation)
13. [Demo script](#13-demo-script)
14. [Limitations to document honestly](#14-limitations-to-document-honestly)
15. [Evidence to collect for the team-authored submission](#15-evidence-to-collect-for-the-team-authored-submission)
16. [Master checklist](#16-master-checklist)

---

## 1. Product definition and guardrails

**One-line definition:** SHADOWNET loads transaction records and reported fraud cases from several (simulated) banks, discovers hidden links between separate cases, fingerprints suspicious money-movement behaviour so that cases with *no shared accounts* can still be matched, reconstructs money trails, and gives explainable *priority-for-review* assessments for new scenarios.

**The "Missing Link" (core innovation):** direct account-connection analysis + Suspicious Pattern Fingerprinting.

**The demo moment to build everything around:**

1. Three simulated cases from different banks (A, B, C) enter the system.
2. SHADOWNET finds a shared intermediary account and shows the transaction trail.
3. A fourth case (D), with completely different accounts, is matched by behaviour.
4. Control cases (E, F) are *not* wrongly linked.
5. A new simulated case is assessed in the Early Warning screen, with reasons.

### Guardrails (must appear in code, UI and documentation) **[R1-FIX]**

| Rule | How to implement |
|---|---|
| Findings are investigative leads, not proof | Persistent banner on every dashboard page; limitations section |
| No autonomous blocking, no guilt declaration | No "block/freeze" buttons or endpoints; no verdict labels |
| Neutral language | Use **risk level** and **priority for review** (Low / Medium / High). Never "fraudster", "guilty", "confirmed fraud" |
| Synthetic data clearly labelled | `source` column, a "SYNTHETIC DATA" badge in the UI |
| Cross-bank assumption stated | "This prototype simulates a shared intelligence view across banks. A real deployment would need data-sharing agreements and privacy controls." |

Banner text (reuse everywhere):

> "SHADOWNET outputs are investigative leads for human review, not proof of criminal activity. The system does not block payments or determine guilt. All data shown is synthetic."

---

## 2. Changes integrated from the alignment review

| # | Review suggestion | Where it is built in |
|---|---|---|
| 1 | Use a public research dataset (or justify synthetic-only) | Section 7.4: public baseline loader; clearly labelled `source` column |
| 2 | "Upload" step in the workflow | `POST /upload-transactions` (Section 10.3) and Upload page (Section 10.5) |
| 3 | Intermediary usage as a fingerprint feature | `n_passthrough`, `hop_depth`, `retention`, layer profile (Section 9.2) |
| 4 | Responsible-use framing | Guardrails above; `DisclaimerBanner` component; risk-level wording |
| 5 | Prioritise cases for review | Ranked case list on Overview (`GET /cases` sorted by risk) |
| 6 | Cross-bank framing | Schema has `sender_bank` + `receiver_bank`; assumption text in UI and docs |
| 7 | Don't overclaim from synthetic data | Control, near-miss and hub-trap cases; honest false-positive reporting (Section 12) |
| 8 | Team authors the submission | Section 15 lists evidence only |

Extra design improvements made while merging:

- The original schema had a single `bank_name`. Cross-bank transfers need **both** `sender_bank` and `receiver_bank`. This is changed here.
- Added a **hub-degree filter** so a popular utility/merchant account does not create false case links.
- Added **normal clusters** (`NORM_xx`) so the scaler and Isolation Forest have a meaningful reference population.

---

## 3. Team roles and ownership

| Member | Role | Owns | Hands off to |
|---|---|---|---|
| M1 | Data engineering | `dataset/`, `data_generator.py`, validation, ground truth, `documentation/dataset_description.md` | M2, M3 |
| M2 | Graph intelligence | `graph_engine.py`, `cross_case_detection.py`, `money_flow.py`, `tests/test_graph.py` | M4 |
| M3 | Pattern and risk | `feature_extraction.py`, `fingerprint_engine.py`, `similarity_engine.py`, `anomaly_detection.py`, `risk_assessment.py`, `tests/test_patterns.py` | M4 |
| M4 | Product | `main.py`, `frontend/`, `tests/test_integration.py`, `documentation/architecture.md`, `demo_script.md` | Everyone |

Dependency chain: **M1 dataset -> M2 graph + M3 patterns -> M4 dashboard.**

Working rules:

- One shared GitHub repo; each person works on a branch named `m1-data`, `m2-graph`, `m3-ai`, `m4-ui`.
- Merge to `main` through pull requests; at least one other member reviews.
- **The data contract (Section 6) is frozen at end of Day 1.** Changes need all four members' agreement.
- Never commit secrets or real personal/banking data.

---

## 4. Environment setup

### 4.1 Prerequisites

- Python 3.10+ and `pip`
- Node.js 18+ and `npm`
- Git

### 4.2 Create the repo and backend environment

```bash
mkdir SHADOWNET && cd SHADOWNET
git init
python -m venv .venv
# macOS/Linux
source .venv/bin/activate
# Windows PowerShell
# .venv\Scripts\Activate.ps1
```

`requirements.txt`:

```text
pandas>=2.0
numpy>=1.24
networkx>=3.1
scikit-learn>=1.3
fastapi>=0.110
uvicorn[standard]>=0.27
python-multipart>=0.0.9
pytest>=7.4
httpx>=0.26
```

```bash
pip install -r requirements.txt
pip freeze > requirements.lock.txt   # exact versions for reproducibility
```

### 4.3 Frontend scaffold (Member 4)

```bash
npm create vite@latest frontend -- --template react
cd frontend
npm install
npm install cytoscape axios react-router-dom recharts
cd ..
```

### 4.4 Offline requirement

The demo must run **without internet**. After `npm install` and `pip install`, nothing should call an external URL at runtime. Do not load fonts/CDNs from the web in the frontend. Bundle everything.

---

## 5. Repository structure

```text
SHADOWNET/
├── dataset/
│   ├── data_generator.py          # M1
│   ├── load_public_baseline.py    # M1  [R1-FIX]
│   ├── validate_dataset.py        # M1
│   ├── transactions.csv           # generated
│   ├── cases.csv                  # generated
│   ├── ground_truth.csv           # generated
│   └── public_baseline_sample.csv # small bundled sample of public data
├── backend/
│   ├── main.py                    # M4
│   ├── state.py                   # M4 (in-memory app state)
│   ├── graph_engine.py            # M2
│   ├── cross_case_detection.py    # M2
│   ├── money_flow.py              # M2
│   ├── feature_extraction.py      # M3
│   ├── fingerprint_engine.py      # M3
│   ├── similarity_engine.py       # M3
│   ├── anomaly_detection.py       # M3
│   └── risk_assessment.py         # M3
├── frontend/
│   └── src/
│       ├── api.js
│       ├── App.jsx
│       ├── components/
│       │   ├── DisclaimerBanner.jsx
│       │   ├── NetworkGraph.jsx
│       │   └── RiskBadge.jsx
│       └── pages/
│           ├── Overview.jsx
│           ├── NetworkExplorer.jsx
│           ├── PatternFingerprinting.jsx
│           ├── MoneyTrail.jsx
│           ├── EarlyWarning.jsx
│           └── Upload.jsx
├── tests/
│   ├── test_graph.py
│   ├── test_patterns.py
│   └── test_integration.py
├── evaluation/
│   ├── evaluate.py                # computes REAL metrics
│   └── results/                   # metrics.json, screenshots/
├── documentation/
│   ├── architecture.md
│   ├── dataset_description.md
│   └── demo_script.md
├── requirements.txt
├── run_demo.sh
└── README.md
```

Because the backend modules import each other, run everything from the repo root (`uvicorn backend.main:app`) and add an empty `backend/__init__.py`.

---

## 6. Data contract (agree on this first)

### 6.1 Transaction schema **[R1-FIX: two bank columns, source column]**

`transactions.csv`

| Column | Type | Example | Notes |
|---|---|---|---|
| `transaction_id` | str | `TX00001` | unique |
| `case_id` | str | `CASE_A` | `CASE_*` = reported case, `NORM_*` = normal cluster, `BACKGROUND` = ordinary traffic |
| `sender_bank` | str | `Bank Alpha` | |
| `receiver_bank` | str | `Bank Beta` | |
| `sender_account` | str | `A101` | |
| `receiver_account` | str | `B900` | |
| `amount` | float | `20000.00` | INR |
| `timestamp` | datetime | `2026-11-01 09:00:00` | ISO format |
| `transaction_type` | str | `Transfer` | |
| `is_synthetic_suspicious` | Yes/No | `Yes` | label for the *simulation*, never used as a model input |
| `source` | str | `synthetic` or `public_paysim` | **[R1-FIX]** clear labelling |

`cases.csv`: `case_id`, `case_type` (`reported_fraud` or `normal_cluster`), `n_transactions`, `start_time`, `end_time`.

`ground_truth.csv`: `case_1`, `case_2`, `relation` (`shared_account`, `similar_pattern`, `unrelated`, `hub_only`, `near_miss`), `expect_connected` (Yes/No), `expect_similar` (Yes/No), `notes`.

### 6.2 Graph output (M2 -> M4)

```json
{
  "connections": [
    {
      "case_a": "CASE_A",
      "case_b": "CASE_B",
      "shared_accounts": [
        {"account": "B900", "role": "intermediary", "bank": "Bank Beta"},
        {"account": "G777", "role": "beneficiary", "bank": "Bank Gamma"}
      ],
      "supporting_transactions": ["TX00003", "TX00004", "TX00031"],
      "explanation": "CASE_A and CASE_B both route funds through account B900 (intermediary) and both pay out to G777."
    }
  ],
  "case_groups": [["CASE_A", "CASE_B", "CASE_C"]],
  "ignored_hub_accounts": [{"account": "U001", "total_degree": 47}]
}
```

### 6.3 Pattern output (M3 -> M4)

```json
{
  "pairs": [
    {
      "case_a": "CASE_A",
      "case_b": "CASE_D",
      "similarity": 0.91,
      "is_similar": true,
      "shared_accounts": 0,
      "matching_features": [
        {"feature": "split_ratio", "a": 3, "b": 3},
        {"feature": "log_median_gap_min", "a": 2.4, "b": 2.5}
      ],
      "explanation": "No common accounts, but both cases show rapid fan-out into 3 intermediaries followed by consolidation."
    }
  ],
  "threshold": 0.80
}
```

### 6.4 Risk output (M3 -> M4)

```json
{
  "case_id": "CASE_NEW",
  "risk_score": 0.78,
  "risk_level": "High priority for review",
  "components": {"connection": 0.5, "pattern_similarity": 0.91, "anomaly": 0.74},
  "closest_known_cases": [{"case_id": "CASE_A", "similarity": 0.91}],
  "matched_features": ["split_ratio", "hop_depth", "log_median_gap_min"],
  "reasons": ["Funds fan out to 3 accounts within 30 minutes.", "Behaviour closely resembles CASE_A (similarity 0.91)."],
  "disclaimer": "Investigative lead only; not proof of criminal activity."
}
```

### 6.5 Core Python data-loading function everyone uses

Put in `backend/graph_engine.py` (M2 owns it, everyone imports it):

```python
import pandas as pd

REQUIRED = ["transaction_id", "case_id", "sender_bank", "receiver_bank",
            "sender_account", "receiver_account", "amount", "timestamp",
            "transaction_type", "is_synthetic_suspicious", "source"]

def load_transactions(path_or_buffer) -> pd.DataFrame:
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
```

---

## 7. Member 1: Data engineering & dataset

### 7.1 Goal

Produce a dataset with **known relationships** so the team can measure detection honestly. Definition of done: connected cases, a disconnected-but-similar case, a control case, a near-miss, a hub trap, normal clusters, background traffic, and a ground-truth file.

### 7.2 Scenario design (build exactly this)

The core fraud behaviour ("layered pattern P1"): victims send funds to a first-layer mule, the mule splits funds into several transfers within minutes, second-layer accounts forward to a consolidating cash-out account within about an hour.

| Case | Banks involved | Design | Expected relationship |
|---|---|---|---|
| `CASE_A` | Alpha victims | Pattern P1, intermediary **B900**, cash-out **G777** | Shares B900 with B and C; shares B900 + G777 with B |
| `CASE_B` | Beta victims | Pattern P1, intermediary **B900**, cash-out **G777** | Connected to A and C |
| `CASE_C` | Gamma victims | Pattern P1, intermediary **B900**, cash-out **G888** | Connected to A and B via B900 |
| `CASE_D` | Alpha + Gamma victims | Pattern P1, **all new accounts** | **Similar to A, B, C by behaviour; zero shared accounts** (the Missing Link) |
| `CASE_E` | Alpha victim | One large transfer, held about 2 days, one onward transfer | Control: unrelated, not similar |
| `CASE_F` | Beta victim | Layered structure but **slow** (hours between steps), only 2 layer-2 accounts, cash-out to popular hub **U001** | Near-miss: not connected (hub filtered), not similar (timing differs) |
| `NORM_00..39` | mixed | 40 small normal clusters (1-2 hops, 2-5 transfers, hours/days gaps) | Reference population for scaler and Isolation Forest |
| `BACKGROUND` | mixed | About 400 random ordinary transfers; hub **U001** receives about 40 | Noise; U001 is a high-degree account |

The hub trap: `CASE_A` contains one small payment to **U001**, and so does `CASE_F`. Both cases touch U001, but U001 is a popular account, so a correct engine ignores it.

### 7.3 Generator: `dataset/data_generator.py`

```python
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
```

Run it:

```bash
python dataset/data_generator.py
```

### 7.4 Public research dataset baseline **[R1-FIX]**

Round 1 promised "public research datasets and clearly labelled synthetic multi-case scenarios". Implement a small loader so the claim is true.

1. Download a public synthetic financial dataset yourself, for example **PaySim** (mobile-money simulation) or the **IBM Transactions for Anti-Money Laundering** dataset, both available on Kaggle. **Check each dataset's licence and cite it** in your documentation.
2. Do not ship the full file. Keep a sample (about 2,000-5,000 rows) in `dataset/public_baseline_sample.csv` so the demo works offline.
3. Map the columns and mark every row `source = public_<name>`.

```python
# dataset/load_public_baseline.py  (example for PaySim columns)
import hashlib
import pandas as pd

BANKS = ["Bank Alpha", "Bank Beta", "Bank Gamma"]

def bank_of(account: str) -> str:
    return BANKS[int(hashlib.md5(account.encode()).hexdigest(), 16) % 3]

def load_paysim(path, n=3000, seed=42):
    raw = pd.read_csv(path)
    raw = raw[raw["type"].isin(["TRANSFER", "PAYMENT"])].sample(n, random_state=seed)
    base = pd.Timestamp("2026-11-01 00:00:00")
    out = pd.DataFrame({
        "transaction_id": [f"PUB{i:05d}" for i in range(len(raw))],
        "case_id": "BACKGROUND",
        "sender_bank": raw["nameOrig"].map(bank_of).values,
        "receiver_bank": raw["nameDest"].map(bank_of).values,
        "sender_account": raw["nameOrig"].values,
        "receiver_account": raw["nameDest"].values,
        "amount": raw["amount"].clip(lower=1).values,
        "timestamp": (base + pd.to_timedelta(raw["step"].values, unit="h")),
        "transaction_type": raw["type"].str.title().values,
        "is_synthetic_suspicious": "No",
        "source": "public_paysim",
    })
    return out
```

How it is used: append these rows to `transactions.csv` as extra ordinary traffic and use their amount/time distributions as additional context for normalisation. If your team decides **not** to use a public dataset, write one honest paragraph explaining that fully controlled synthetic data was chosen so that ground truth is known, and state that public data cannot provide labelled cross-case relationships.

### 7.5 Validation: `dataset/validate_dataset.py`

```python
import sys
import pandas as pd

def validate(path="dataset/transactions.csv", gt="dataset/ground_truth.csv"):
    df = pd.read_csv(path, parse_dates=["timestamp"])
    checks = {
        "no nulls": not df.isnull().any().any(),
        "unique transaction ids": df.transaction_id.is_unique,
        "amounts positive": (df.amount > 0).all(),
        "no self-transfers": (df.sender_account != df.receiver_account).all(),
        "three banks present": set(df.sender_bank) >= {"Bank Alpha", "Bank Beta", "Bank Gamma"},
        "B900 appears in A, B, C": set(
            df[(df.sender_account == "B900") | (df.receiver_account == "B900")].case_id
        ) >= {"CASE_A", "CASE_B", "CASE_C"},
        "CASE_D shares no accounts with A/B/C": _no_overlap(df),
        "normal clusters >= 30": df.case_id.str.startswith("NORM_").sum() > 0
            and df[df.case_id.str.startswith("NORM_")].case_id.nunique() >= 30,
        "ground truth exists": len(pd.read_csv(gt)) == 15,
    }
    for k, v in checks.items():
        print(("PASS " if v else "FAIL ") + k)
    return all(checks.values())

def _accounts(df, case):
    c = df[df.case_id == case]
    return set(c.sender_account) | set(c.receiver_account)

def _no_overlap(df):
    d = _accounts(df, "CASE_D")
    return all(not (d & _accounts(df, c)) for c in ["CASE_A", "CASE_B", "CASE_C"])

if __name__ == "__main__":
    sys.exit(0 if validate() else 1)
```

### 7.6 Member 1 deliverables

- `data_generator.py`, `load_public_baseline.py`, `validate_dataset.py`
- `transactions.csv`, `cases.csv`, `ground_truth.csv`, `public_baseline_sample.csv`
- `documentation/dataset_description.md`: scenarios, columns, how ground truth is defined, public dataset name/licence, "synthetic" statement
- A short validation report (paste the validator output)

---

## 8. Member 2: Graph intelligence & money flow

### 8.1 Goal

Reveal hidden links between cases and reconstruct fund movement. Definition of done: for A, B, C the engine reports shared intermediary **B900**, shows supporting transaction IDs, groups the cases, and **ignores hub U001**.

### 8.2 `backend/graph_engine.py`: build the graph

```python
import networkx as nx
import pandas as pd

# (load_transactions from Section 6.5 lives in this file too)

def build_graph(df: pd.DataFrame, cases=None) -> nx.MultiDiGraph:
    """Accounts = nodes; transfers = directed, timestamped edges."""
    d = df if cases is None else df[df.case_id.isin(cases)]
    G = nx.MultiDiGraph()
    for r in d.itertuples(index=False):
        G.add_node(r.sender_account, bank=r.sender_bank)
        G.add_node(r.receiver_account, bank=r.receiver_bank)
        G.add_edge(r.sender_account, r.receiver_account, key=r.transaction_id,
                   transaction_id=r.transaction_id, amount=float(r.amount),
                   timestamp=r.timestamp, case_id=r.case_id,
                   transaction_type=r.transaction_type)
    return G

def graph_to_cytoscape(G: nx.MultiDiGraph, highlight_accounts=()) -> dict:
    hl = set(highlight_accounts)
    nodes = [{"data": {"id": n, "label": n, "bank": a.get("bank", ""),
                       "shared": n in hl}} for n, a in G.nodes(data=True)]
    edges = [{"data": {"id": k, "source": u, "target": v,
                       "label": f"₹{d['amount']:,.0f}",
                       "case_id": d["case_id"],
                       "timestamp": d["timestamp"].strftime("%Y-%m-%d %H:%M:%S")}}
             for u, v, k, d in G.edges(keys=True, data=True)]
    return {"nodes": nodes, "edges": edges}
```

### 8.3 `backend/cross_case_detection.py`: shared accounts and case groups

Key ideas:

- Only look at `reported_fraud` cases (`CASE_*`).
- Compute each account's **total degree over all transactions** (including background). If above the hub threshold, it is a popular account: record it under `ignored_hub_accounts` and do not use it as a link.
- Classify the role per account: `intermediary` (receives and sends), `beneficiary` (only receives), `source` (only sends).

```python
from itertools import combinations
import networkx as nx
import pandas as pd

HUB_DEGREE_THRESHOLD = 25   # tune against your data; document the value

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
    reported = df[df.case_id.str.startswith("CASE_")]
    total_deg = pd.concat([df.sender_account, df.receiver_account]).value_counts()
    ac = _account_cases(reported)

    bank_of = {}
    for r in df.itertuples():
        bank_of[r.sender_account] = r.sender_bank
        bank_of[r.receiver_account] = r.receiver_bank

    ignored, shared_by_account = [], {}
    for account, sub in ac.groupby("account"):
        cases = sorted(sub.case_id.unique())
        if len(cases) < 2:
            continue
        if total_deg[account] > hub_threshold:
            ignored.append({"account": account, "total_degree": int(total_deg[account])})
            continue
        shared_by_account[account] = {
            "cases": cases, "df": sub,
            "role": _role(sub)}

    connections = {}
    for account, info in shared_by_account.items():
        for a, b in combinations(info["cases"], 2):
            c = connections.setdefault((a, b), {"shared_accounts": [], "supporting": set()})
            c["shared_accounts"].append(
                {"account": account, "role": info["role"], "bank": bank_of[account]})
            sub = info["df"]
            c["supporting"] |= set(sub[sub.case_id.isin([a, b])].transaction_id)

    out = []
    for (a, b), c in sorted(connections.items()):
        names = ", ".join(f"{x['account']} ({x['role']})" for x in c["shared_accounts"])
        out.append({"case_a": a, "case_b": b,
                    "shared_accounts": c["shared_accounts"],
                    "supporting_transactions": sorted(c["supporting"]),
                    "explanation": f"{a} and {b} both involve {names}."})

    H = nx.Graph()
    H.add_nodes_from(reported.case_id.unique())
    H.add_edges_from((c["case_a"], c["case_b"]) for c in out)
    groups = [sorted(g) for g in nx.connected_components(H) if len(g) > 1]
    return {"connections": out, "case_groups": groups, "ignored_hub_accounts": ignored}
```

Also expose helper functions the dashboard needs: `repeated_beneficiaries(...)` (shared accounts with role `beneficiary`) and `common_intermediaries(...)` (role `intermediary`), simply by filtering the `shared_accounts` list.

### 8.4 `backend/money_flow.py`: reconstruct trails

```python
import networkx as nx
import pandas as pd

def chronological_trail(case_df: pd.DataFrame) -> list[dict]:
    d = case_df.sort_values("timestamp")
    return [{"transaction_id": r.transaction_id, "time": r.timestamp.isoformat(),
             "from": r.sender_account, "to": r.receiver_account,
             "amount": float(r.amount), "from_bank": r.sender_bank,
             "to_bank": r.receiver_bank} for r in d.itertuples()]

def detect_splitting(case_df, window_min=30, min_targets=3) -> list[dict]:
    """A sender that pays >= min_targets distinct receivers within window_min minutes."""
    out = []
    for sender, g in case_df.sort_values("timestamp").groupby("sender_account"):
        g = g.reset_index(drop=True)
        for i in range(len(g)):
            w = g[(g.timestamp >= g.timestamp[i]) &
                  (g.timestamp <= g.timestamp[i] + pd.Timedelta(minutes=window_min))]
            if w.receiver_account.nunique() >= min_targets:
                out.append({"account": sender,
                            "targets": sorted(w.receiver_account.unique()),
                            "total": float(w.amount.sum()),
                            "transaction_ids": list(w.transaction_id)})
                break
    return out

def detect_consolidation(case_df, window_min=120, min_sources=3) -> list[dict]:
    """A receiver that gets funds from >= min_sources distinct senders within window_min."""
    out = []
    for receiver, g in case_df.sort_values("timestamp").groupby("receiver_account"):
        g = g.reset_index(drop=True)
        for i in range(len(g)):
            w = g[(g.timestamp >= g.timestamp[i]) &
                  (g.timestamp <= g.timestamp[i] + pd.Timedelta(minutes=window_min))]
            if w.sender_account.nunique() >= min_sources:
                out.append({"account": receiver,
                            "sources": sorted(w.sender_account.unique()),
                            "total": float(w.amount.sum()),
                            "transaction_ids": list(w.transaction_id)})
                break
    return out

def time_respecting_paths(case_df, max_depth=6) -> list[dict]:
    """Paths source -> destination where every hop happens after the previous hop."""
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
    return [{"accounts": [p[0].sender_account] + [e.receiver_account for e in p],
             "transaction_ids": [e.transaction_id for e in p],
             "amount_entering": float(p[0].amount),
             "amount_leaving": float(p[-1].amount),
             "duration_min": round((p[-1].timestamp - p[0].timestamp).total_seconds() / 60, 1)}
            for p in paths]

def money_trail(case_df) -> dict:
    return {"trail": chronological_trail(case_df),
            "splits": detect_splitting(case_df),
            "consolidations": detect_consolidation(case_df),
            "paths": time_respecting_paths(case_df)}
```

### 8.5 Tests: `tests/test_graph.py`

```python
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
    assert any(h["account"] == "A" + "U001" for h in out["ignored_hub_accounts"])
    pairs = {(c["case_a"], c["case_b"]) for c in out["connections"]}
    assert ("CASE_A", "CASE_F") not in pairs

def test_case_d_not_connected_by_accounts():
    out = discover_connections(df)
    assert all("CASE_D" not in (c["case_a"], c["case_b"]) for c in out["connections"])

def test_split_detected():
    r = money_trail(df[df.case_id == "CASE_A"])
    assert len(r["splits"]) >= 1 and len(r["paths"]) >= 1
```

> Note: the hub account ID is `A` + `U001` = `AU001` because `acct()` prefixes the bank letter. Check the generated ID in `transactions.csv` and use it consistently.

### 8.6 Member 2 deliverables

- `graph_engine.py`, `cross_case_detection.py`, `money_flow.py`
- Graph analysis output as JSON (`evaluation/results/graph_output.json`)
- Test results on M1's dataset

---

## 9. Member 3: Pattern fingerprinting & risk assessment

### 9.1 Goal

Match cases by **behaviour** even with no common accounts, avoid linking controls and near-misses, and give explainable priority-for-review assessments. A feature-based similarity engine is the right first implementation (no GNN needed).

### 9.2 `backend/feature_extraction.py`

Features per case (computed on that case's own transactions only):

| Feature | Meaning |
|---|---|
| `log_avg_amount` | log(1 + average transfer amount) |
| `n_tx` | number of transfers |
| `log_median_gap_min` | log(1 + median minutes between consecutive transfers) (speed) |
| `log_duration_min` | log(1 + minutes from first to last transfer) |
| `split_ratio` | maximum number of distinct receivers paid by one account |
| `n_beneficiaries` | accounts that only receive (terminal receivers) |
| `in_out_ratio` | fraction of source money that reaches terminal accounts |
| `n_passthrough` | **[R1-FIX]** accounts that both receive and send (intermediary usage) |
| `hop_depth` | **[R1-FIX]** length of the longest transfer chain |
| `retention` | **[R1-FIX]** forwarded amount / received amount at pass-through accounts |
| `consolidation_ratio` | maximum number of distinct senders into one non-source account |
| `layer_0..layer_3` | transaction-sequence profile: share of transfers at each hop depth |

```python
import numpy as np
import pandas as pd
import networkx as nx

FEATURES = ["log_avg_amount", "n_tx", "log_median_gap_min", "log_duration_min",
            "split_ratio", "n_beneficiaries", "in_out_ratio", "n_passthrough",
            "hop_depth", "retention", "consolidation_ratio",
            "layer_0", "layer_1", "layer_2", "layer_3"]

def case_features(c: pd.DataFrame) -> dict:
    c = c.sort_values("timestamp")
    n = len(c)
    senders, receivers = set(c.sender_account), set(c.receiver_account)
    passthrough = senders & receivers
    sources = senders - receivers
    terminals = receivers - senders

    gaps = c.timestamp.diff().dropna().dt.total_seconds() / 60
    median_gap = float(gaps.median()) if len(gaps) else 0.0
    duration = (c.timestamp.max() - c.timestamp.min()).total_seconds() / 60

    # hop depth via the (time-ordered) DAG
    G = nx.DiGraph()
    G.add_edges_from(zip(c.sender_account, c.receiver_account))
    try:
        depth = nx.dag_longest_path_length(G)
    except nx.NetworkXUnfeasible:      # cycle: fall back to node count
        depth = len(G.nodes) - 1

    # layer profile: depth of each transaction's sender from a source
    level = {s: 0 for s in sources}
    for u in nx.topological_sort(G) if nx.is_directed_acyclic_graph(G) else []:
        for v in G.successors(u):
            level[v] = max(level.get(v, 0), level.get(u, 0) + 1)
    layers = np.zeros(4)
    for s in c.sender_account:
        layers[min(level.get(s, 0), 3)] += 1
    layers = layers / max(n, 1)

    out_deg = c.groupby("sender_account").receiver_account.nunique()
    in_deg = c.groupby("receiver_account").sender_account.nunique()
    src_amt = c[c.sender_account.isin(sources)].amount.sum()
    term_amt = c[c.receiver_account.isin(terminals)].amount.sum()
    recv_pt = c[c.receiver_account.isin(passthrough)].amount.sum()
    send_pt = c[c.sender_account.isin(passthrough)].amount.sum()

    return {
        "log_avg_amount": float(np.log1p(c.amount.mean())),
        "n_tx": n,
        "log_median_gap_min": float(np.log1p(median_gap)),
        "log_duration_min": float(np.log1p(duration)),
        "split_ratio": int(out_deg.max()) if len(out_deg) else 0,
        "n_beneficiaries": len(terminals),
        "in_out_ratio": float(term_amt / src_amt) if src_amt else 0.0,
        "n_passthrough": len(passthrough),
        "hop_depth": int(depth),
        "retention": float(send_pt / recv_pt) if recv_pt else 0.0,
        "consolidation_ratio": int(in_deg[in_deg.index.isin(passthrough | terminals)].max())
                               if len(in_deg) else 0,
        **{f"layer_{i}": float(layers[i]) for i in range(4)},
    }

def all_case_features(df: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for cid, g in df[~df.case_id.isin(["BACKGROUND"])].groupby("case_id"):
        rows.append({"case_id": cid, **case_features(g)})
    return pd.DataFrame(rows).set_index("case_id")[FEATURES]
```

### 9.3 `backend/fingerprint_engine.py`: fingerprints with proper normalisation

A tiny set of cases makes naive scaling unreliable, so:

1. Fit the scaler on the **reference pool**: all `NORM_*` clusters plus all reported cases.
2. Optionally create jittered copies of reported cases (amounts x 0.9-1.1, times x 0.8-1.2) to widen the pool and to **calibrate** the threshold on variation.

```python
import numpy as np
import pandas as pd
from sklearn.preprocessing import StandardScaler
from backend.feature_extraction import all_case_features, FEATURES

class FingerprintEngine:
    def __init__(self, df: pd.DataFrame):
        self.features = all_case_features(df)
        self.scaler = StandardScaler().fit(self.features.values)
        z = self.scaler.transform(self.features.values)
        self.fingerprints = pd.DataFrame(z, index=self.features.index, columns=FEATURES)

    def fingerprint_of(self, feature_row: dict) -> np.ndarray:
        x = np.array([[feature_row[f] for f in FEATURES]])
        return self.scaler.transform(x)[0]
```

### 9.4 `backend/similarity_engine.py`: compare behaviour, not account names

```python
import numpy as np
from itertools import combinations
from backend.feature_extraction import FEATURES

def similarity(za: np.ndarray, zb: np.ndarray) -> float:
    """Combined score in [0,1]: cosine (shape) and inverse distance (magnitude)."""
    cos = float(np.dot(za, zb) / (np.linalg.norm(za) * np.linalg.norm(zb) + 1e-9))
    dist = float(np.linalg.norm(za - zb)) / np.sqrt(len(za))
    return 0.5 * ((cos + 1) / 2) + 0.5 * (1 / (1 + dist))

def matching_features(za, zb, raw_a, raw_b, tol=0.5, top=5):
    """Features where the standardised values are close, i.e. why they look alike."""
    diffs = [(abs(za[i] - zb[i]), FEATURES[i]) for i in range(len(FEATURES))]
    diffs.sort()
    return [{"feature": f, "a": round(float(raw_a[f]), 3), "b": round(float(raw_b[f]), 3)}
            for d, f in diffs[:top] if d <= tol]

def compare_all(engine, reported_ids, threshold):
    out = []
    for a, b in combinations(reported_ids, 2):
        s = similarity(engine.fingerprints.loc[a].values, engine.fingerprints.loc[b].values)
        out.append({"case_a": a, "case_b": b, "similarity": round(s, 3),
                    "is_similar": s >= threshold,
                    "matching_features": matching_features(
                        engine.fingerprints.loc[a].values, engine.fingerprints.loc[b].values,
                        engine.features.loc[a], engine.features.loc[b])})
    return out

def calibrate_threshold(engine, ground_truth):
    """Pick a threshold in the gap between the lowest similar pair and the highest dissimilar pair.
    Report the margin: if the gap is tiny or negative, say so honestly."""
    sims, dis = [], []
    for r in ground_truth.itertuples():
        s = similarity(engine.fingerprints.loc[r.case_1].values,
                       engine.fingerprints.loc[r.case_2].values)
        (sims if r.expect_similar == "Yes" else dis).append(s)
    lo, hi = min(sims), max(dis)
    return {"threshold": round((lo + hi) / 2, 3), "min_similar": round(lo, 3),
            "max_dissimilar": round(hi, 3), "margin": round(lo - hi, 3)}
```

Important honesty point: because you wrote the scenarios, a clean separation is expected. Report the *margin*, and run the stress variants described in Section 12.4.

### 9.5 `backend/anomaly_detection.py`: Isolation Forest

Train on **normal clusters only**, then score every case. Reported cases should score as more anomalous than normal clusters.

```python
import numpy as np
from sklearn.ensemble import IsolationForest

class AnomalyScorer:
    def __init__(self, engine):
        normal_ids = [c for c in engine.fingerprints.index if c.startswith("NORM_")]
        X = engine.fingerprints.loc[normal_ids].values
        self.model = IsolationForest(n_estimators=200, contamination="auto", random_state=42).fit(X)
        raw = -self.model.score_samples(engine.fingerprints.values)   # higher = more anomalous
        self._lo, self._hi = float(raw.min()), float(raw.max())

    def score(self, z: np.ndarray) -> float:
        raw = -self.model.score_samples(z.reshape(1, -1))[0]
        return float(np.clip((raw - self._lo) / (self._hi - self._lo + 1e-9), 0, 1))
```

### 9.6 `backend/risk_assessment.py`: explainable priority for review

A transparent, documented heuristic (do **not** present it as a trained model):

```
risk_score = 0.40 * connection + 0.35 * pattern_similarity + 0.25 * anomaly
```

- `connection` = min(1, number of non-hub shared accounts with known cases / 2)
- `pattern_similarity` = highest similarity to any known reported case
- `anomaly` = Isolation Forest score (0-1)

| Score | Level wording |
|---|---|
| >= 0.65 | High priority for review |
| 0.35 to 0.65 | Medium priority for review |
| < 0.35 | Low priority for review |

```python
from backend.similarity_engine import similarity, matching_features
from backend.feature_extraction import case_features

DISCLAIMER = "Investigative lead only; not proof of criminal activity."

def level(score):
    if score >= 0.65: return "High priority for review"
    if score >= 0.35: return "Medium priority for review"
    return "Low priority for review"

def assess_case(case_df, engine, anomaly, known_ids, threshold, existing_df=None, hub_threshold=25):
    feats = case_features(case_df)
    z = engine.fingerprint_of(feats)

    sims = sorted(((similarity(z, engine.fingerprints.loc[k].values), k) for k in known_ids),
                  reverse=True)
    best_sim, best_id = sims[0]
    a_score = anomaly.score(z)

    # direct connection: accounts shared with known reported cases (hubs ignored)
    shared = 0
    if existing_df is not None:
        known = existing_df[existing_df.case_id.isin(known_ids)]
        deg = known.sender_account.append(known.receiver_account).value_counts() \
            if hasattr(known.sender_account, "append") else None
        import pandas as pd
        deg = pd.concat([existing_df.sender_account, existing_df.receiver_account]).value_counts()
        mine = set(case_df.sender_account) | set(case_df.receiver_account)
        theirs = set(known.sender_account) | set(known.receiver_account)
        shared = len([a for a in mine & theirs if deg[a] <= hub_threshold])

    connection = min(1.0, shared / 2)
    score = 0.40 * connection + 0.35 * best_sim + 0.25 * a_score

    matched = matching_features(z, engine.fingerprints.loc[best_id].values,
                                feats, engine.features.loc[best_id])
    reasons = []
    if shared:
        reasons.append(f"Shares {shared} non-hub account(s) with previously reported cases.")
    if best_sim >= threshold:
        reasons.append(f"Behaviour closely resembles {best_id} (similarity {best_sim:.2f}).")
    if feats["split_ratio"] >= 3:
        reasons.append(f"Funds fan out to {feats['split_ratio']} accounts from a single account.")
    if feats["log_median_gap_min"] < 3.5:
        reasons.append("Transfers occur in rapid succession.")
    if a_score > 0.6:
        reasons.append("Behaviour is unusual compared with the normal reference population.")
    if not reasons:
        reasons.append("No strong similarity or connection to known cases was found.")

    return {"risk_score": round(score, 3), "risk_level": level(score),
            "components": {"connection": round(connection, 2),
                           "pattern_similarity": round(best_sim, 2),
                           "anomaly": round(a_score, 2)},
            "closest_known_cases": [{"case_id": k, "similarity": round(s, 2)} for s, k in sims[:3]],
            "matched_features": [m["feature"] for m in matched],
            "reasons": reasons, "disclaimer": DISCLAIMER}
```

> Simplify the `deg` lines when you write this file: keep only the `pd.concat(...)` version; the `.append` branch is shown only to remind you that pandas 2.x removed `Series.append`.

### 9.7 Early-warning simulation (Task 5)

`POST /simulate-risk` accepts a list of new synthetic transactions (same schema, `case_id = "CASE_NEW"`). The backend builds a DataFrame, calls `assess_case`, and returns the Section 6.4 JSON. Prepare **three** ready-made scenarios for the demo:

1. **Looks like the known pattern:** fan-out into 3 accounts within minutes (expect High).
2. **Shares B900:** one transfer into the shared intermediary (expect connection component > 0).
3. **Ordinary payments:** two slow, small transfers (expect Low).

### 9.8 Tests: `tests/test_patterns.py`

```python
import pandas as pd
from backend.graph_engine import load_transactions
from backend.fingerprint_engine import FingerprintEngine
from backend.similarity_engine import similarity, calibrate_threshold

df = load_transactions("dataset/transactions.csv")
gt = pd.read_csv("dataset/ground_truth.csv")
eng = FingerprintEngine(df)
cal = calibrate_threshold(eng, gt)

def sim(a, b):
    return similarity(eng.fingerprints.loc[a].values, eng.fingerprints.loc[b].values)

def test_case_d_similar_to_a():
    assert sim("CASE_A", "CASE_D") >= cal["threshold"]

def test_controls_not_matched():
    assert sim("CASE_A", "CASE_E") < cal["threshold"]
    assert sim("CASE_A", "CASE_F") < cal["threshold"]

def test_positive_margin():
    assert cal["margin"] > 0
```

### 9.9 Member 3 deliverables

- The five engine files, evaluation output (similarity matrix, calibrated threshold and margin, anomaly scores of reported vs normal)
- Written note: features chosen, scaling method, what the risk score is and is not

---

## 10. Member 4: Backend API, dashboard & integration

### 10.1 Goal

A judge opens the dashboard, loads sample cases, discovers connections, compares patterns and inspects evidence, with no code. Start Day 1 with a skeleton that serves **mock JSON** from Section 6, and swap in real engines as they land.

### 10.2 `backend/state.py`: in-memory state

```python
import pandas as pd
from backend.graph_engine import load_transactions
from backend.cross_case_detection import discover_connections
from backend.fingerprint_engine import FingerprintEngine
from backend.anomaly_detection import AnomalyScorer
from backend.similarity_engine import calibrate_threshold, compare_all
from backend.risk_assessment import assess_case

class State:
    def load(self, df: pd.DataFrame, ground_truth_path="dataset/ground_truth.csv"):
        self.df = df
        self.graph_result = discover_connections(df)
        self.engine = FingerprintEngine(df)
        self.anomaly = AnomalyScorer(self.engine)
        self.reported = sorted(c for c in df.case_id.unique() if c.startswith("CASE_"))
        try:
            gt = pd.read_csv(ground_truth_path)
            self.cal = calibrate_threshold(self.engine, gt)
        except Exception:
            self.cal = {"threshold": 0.80}
        self.pairs = compare_all(self.engine, self.reported, self.cal["threshold"])
        self.case_risk = {}
        for cid in self.reported:
            others = [c for c in self.reported if c != cid]
            self.case_risk[cid] = assess_case(
                df[df.case_id == cid], self.engine, self.anomaly, others,
                self.cal["threshold"], existing_df=df[~df.case_id.eq(cid)])

state = State()
```

### 10.3 `backend/main.py`: FastAPI endpoints

| Endpoint | Purpose |
|---|---|
| `GET /health` | liveness check |
| `GET /overview` | totals: cases, accounts, transactions, relationships; disclaimer text |
| `GET /cases` | reported cases **ranked by risk score** (priority queue) **[R1-FIX]** |
| `GET /transactions?case_id=` | transactions, optionally per case |
| `GET /graph?cases=CASE_A,CASE_B` | Cytoscape nodes/edges, shared accounts highlighted |
| `POST /upload-transactions` | upload a CSV and reload state **[R1-FIX]** |
| `POST /discover-connections` | Section 6.2 output |
| `POST /compare-patterns` | Section 6.3 output |
| `GET /money-trail/{case_id}` | trail, splits, consolidations, paths |
| `POST /simulate-risk` | Section 6.4 output for a new scenario |

```python
import io
import pandas as pd
from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from backend.graph_engine import load_transactions, build_graph, graph_to_cytoscape
from backend.money_flow import money_trail
from backend.risk_assessment import assess_case
from backend.state import state

app = FastAPI(title="SHADOWNET API")
app.add_middleware(CORSMiddleware, allow_origins=["http://localhost:5173"],
                   allow_methods=["*"], allow_headers=["*"])

DISCLAIMER = ("SHADOWNET outputs are investigative leads for human review, not proof of "
              "criminal activity. The system does not block payments or determine guilt. "
              "All data shown is synthetic.")

@app.on_event("startup")
def startup():
    state.load(load_transactions("dataset/transactions.csv"))

@app.get("/health")
def health():
    return {"status": "ok"}

@app.get("/overview")
def overview():
    df = state.df
    return {"cases": len(state.reported),
            "accounts": int(pd.concat([df.sender_account, df.receiver_account]).nunique()),
            "transactions": len(df),
            "relationships": len(state.graph_result["connections"]),
            "similar_pairs": sum(p["is_similar"] for p in state.pairs),
            "disclaimer": DISCLAIMER}

@app.get("/cases")
def cases():
    rows = [{"case_id": c, **state.case_risk[c]} for c in state.reported]
    return sorted(rows, key=lambda r: r["risk_score"], reverse=True)

@app.get("/transactions")
def transactions(case_id: str | None = None):
    d = state.df if case_id is None else state.df[state.df.case_id == case_id]
    return d.assign(timestamp=d.timestamp.astype(str)).to_dict("records")

@app.get("/graph")
def graph(cases: str):
    ids = cases.split(",")
    G = build_graph(state.df, ids)
    shared = {s["account"] for c in state.graph_result["connections"]
              if c["case_a"] in ids and c["case_b"] in ids for s in c["shared_accounts"]}
    return graph_to_cytoscape(G, shared)

@app.post("/upload-transactions")
async def upload(file: UploadFile = File(...)):
    try:
        df = load_transactions(io.BytesIO(await file.read()))
    except Exception as e:
        raise HTTPException(400, f"Invalid file: {e}")
    state.load(df)
    return {"status": "loaded", "transactions": len(df), "cases": len(state.reported)}

@app.post("/discover-connections")
def discover():
    return state.graph_result

@app.post("/compare-patterns")
def compare():
    return {"pairs": state.pairs, "threshold": state.cal["threshold"]}

@app.get("/money-trail/{case_id}")
def trail(case_id: str):
    d = state.df[state.df.case_id == case_id]
    if d.empty:
        raise HTTPException(404, "Unknown case")
    return money_trail(d)

class Tx(BaseModel):
    sender_account: str
    receiver_account: str
    amount: float
    timestamp: str
    sender_bank: str = "Bank Alpha"
    receiver_bank: str = "Bank Alpha"

@app.post("/simulate-risk")
def simulate(txs: list[Tx]):
    rows = [dict(transaction_id=f"SIM{i:03d}", case_id="CASE_NEW",
                 transaction_type="Transfer", is_synthetic_suspicious="Yes",
                 source="simulation", **t.model_dump()) for i, t in enumerate(txs)]
    new = pd.DataFrame(rows)
    new["timestamp"] = pd.to_datetime(new["timestamp"])
    result = assess_case(new, state.engine, state.anomaly, state.reported,
                         state.cal["threshold"], existing_df=state.df)
    return {"case_id": "CASE_NEW", **result}
```

Run:

```bash
uvicorn backend.main:app --reload --port 8000
# API docs automatically at http://localhost:8000/docs
```

### 10.4 Frontend foundation

`src/api.js`:

```javascript
import axios from "axios";
const api = axios.create({ baseURL: "http://localhost:8000" });
export const getOverview = () => api.get("/overview").then(r => r.data);
export const getCases = () => api.get("/cases").then(r => r.data);
export const getGraph = (ids) => api.get("/graph", { params: { cases: ids.join(",") } }).then(r => r.data);
export const discover = () => api.post("/discover-connections").then(r => r.data);
export const comparePatterns = () => api.post("/compare-patterns").then(r => r.data);
export const getTrail = (id) => api.get(`/money-trail/${id}`).then(r => r.data);
export const simulate = (txs) => api.post("/simulate-risk", txs).then(r => r.data);
export const upload = (file) => {
  const f = new FormData(); f.append("file", file);
  return api.post("/upload-transactions", f).then(r => r.data);
};
```

`components/DisclaimerBanner.jsx` **[R1-FIX]**:

```jsx
export default function DisclaimerBanner() {
  return (
    <div style={{ background: "#fff4e5", borderBottom: "1px solid #f0b86e", padding: "8px 16px", fontSize: 13 }}>
      <strong>Investigative leads only.</strong> SHADOWNET outputs are for human review, not proof of
      criminal activity. The system does not block payments or determine guilt.
      <span style={{ marginLeft: 12, background: "#444", color: "#fff", padding: "2px 8px", borderRadius: 4 }}>
        SYNTHETIC DATA
      </span>
    </div>
  );
}
```

`components/NetworkGraph.jsx` (Cytoscape directly):

```jsx
import { useEffect, useRef } from "react";
import cytoscape from "cytoscape";

const BANK_COLOR = { "Bank Alpha": "#2b6cb0", "Bank Beta": "#2f855a", "Bank Gamma": "#b7791f" };

export default function NetworkGraph({ elements, onNodeClick }) {
  const ref = useRef(null);
  useEffect(() => {
    if (!elements) return;
    const cy = cytoscape({
      container: ref.current,
      elements: [...elements.nodes, ...elements.edges],
      layout: { name: "cose", animate: false },
      style: [
        { selector: "node", style: {
            label: "data(label)", "font-size": 9, "text-valign": "bottom",
            "background-color": ele => BANK_COLOR[ele.data("bank")] || "#718096" } },
        { selector: "node[?shared]", style: {
            shape: "diamond", width: 36, height: 36,
            "border-width": 3, "border-color": "#e53e3e" } },
        { selector: "edge", style: {
            width: 2, "curve-style": "bezier", "target-arrow-shape": "triangle",
            label: "data(label)", "font-size": 7, "line-color": "#a0aec0",
            "target-arrow-color": "#a0aec0" } },
      ],
    });
    cy.on("tap", "node", e => onNodeClick && onNodeClick(e.target.data()));
    return () => cy.destroy();
  }, [elements]);
  return <div ref={ref} style={{ width: "100%", height: 520, border: "1px solid #e2e8f0" }} />;
}
```

Legend to include on the page: colour by bank; red-bordered diamond = shared account; edge label = amount.

### 10.5 The six pages

**1. Investigation Overview** (`Overview.jsx`)
- Cards: cases, accounts, transactions, discovered relationships, similar pairs.
- **Ranked case list** (from `GET /cases`) sorted by risk score with `RiskBadge`, so investigators see which case to review first. **[R1-FIX]**
- Link on each row to its Money Trail.

**2. Network Explorer** (`NetworkExplorer.jsx`)
- Multi-select of cases (default A, B, C); calls `/graph`.
- Shared intermediaries shown as red-bordered diamonds; clicking a node shows account, bank, and which cases it appears in.
- Side panel: connection explanations and supporting transaction IDs from `/discover-connections`.
- Small note listing ignored hub accounts and why.

**3. Pattern Fingerprinting** (`PatternFingerprinting.jsx`)
- Similarity matrix/heatmap of reported cases (a simple HTML table with colour scale is enough; `recharts` optional).
- Click a pair: show similarity, threshold, matching features and the explanation. For A vs D show "Shared accounts: 0".
- Radar or bar chart comparing the two fingerprints.

**4. Money Trail** (`MoneyTrail.jsx`)
- Case selector; chronological table of transfers (time, from, to, amount, banks, transaction ID).
- Badges for detected splitting and consolidation; list of time-respecting paths with entering/leaving amounts and duration.
- Optional: render the path as a Cytoscape graph with ordered edge labels (1, 2, 3...).

**5. Early Warning** (`EarlyWarning.jsx`)
- Three preset scenario buttons (Section 9.7) plus editable transaction rows.
- Calls `/simulate-risk`; shows risk level, score, component bars, closest known cases, matched features, reasons list and the disclaimer. No "block" action exists.

**6. Upload** (`Upload.jsx`) **[R1-FIX]**
- File input for a transactions CSV matching the schema, calling `/upload-transactions`.
- Shows schema requirements and the result; a "Reset to sample data" button simply reloads the bundled CSV.
- Test with a deliberately wrong CSV and show the error message.

Routing in `App.jsx`: a sidebar with six links, `DisclaimerBanner` at the top of every page, and a footer line stating the cross-bank assumption.

### 10.6 Run script for a repeatable, offline demo

`run_demo.sh`:

```bash
#!/usr/bin/env bash
set -e
python dataset/data_generator.py
python dataset/validate_dataset.py
pytest -q
uvicorn backend.main:app --port 8000 &
cd frontend && npm run dev
```

Pre-build once with `npm run build` and serve the `dist/` folder if you want to avoid dev-server surprises during judging. Keep a pre-recorded screen capture as a backup.

### 10.7 Integration test: `tests/test_integration.py`

```python
from fastapi.testclient import TestClient
from backend.main import app

def test_endpoints():
    with TestClient(app) as c:
        assert c.get("/health").status_code == 200
        assert c.get("/overview").json()["cases"] >= 6
        cases = c.get("/cases").json()
        scores = [x["risk_score"] for x in cases]
        assert scores == sorted(scores, reverse=True)
        assert len(c.post("/discover-connections").json()["connections"]) >= 3
        assert c.get("/money-trail/CASE_A").status_code == 200
        assert c.get("/money-trail/NOPE").status_code == 404
```

### 10.8 Member 4 deliverables

Working dashboard (six pages), React + Cytoscape source, API integration, `demo_script.md`, `architecture.md` (diagram of: CSV -> loader -> graph engine + fingerprint engine -> FastAPI -> React), screenshots (Section 15).

---

## 11. Schedule: 5-day plan with 3-day and 2-day cuts

### 11.1 Five days

| Day | M1 | M2 | M3 | M4 | Milestone |
|---|---|---|---|---|---|
| 1 | Run generator v0, freeze schema | Define loader + graph input | Define feature list | Repo, FastAPI skeleton serving mock JSON, Vite scaffold, banner | **Data contract frozen** |
| 2 | Finish dataset, public baseline, validator | Graph + shared accounts + hub filter | Feature extraction, similarity, threshold calibration | Network Explorer page | Modules work independently |
| 3 | Validate, ground truth review | Money flow | Isolation Forest, risk assessment, explanations | Wire real APIs; Overview, Fingerprinting, Money Trail pages | End-to-end demo works |
| 4 | Add stress variants and noise | Tests, bug fixes | Evaluate, false connections, margins | Early Warning, Upload, polish, `run_demo.sh` | Reproducible results |
| 5 | Dataset doc | Graph doc and evidence | Model doc and evidence | Screenshots, rehearsal | Evidence pack ready; team writes the PPT/PDF |

### 11.2 If you only have 3 days

Merge Days 1-2 and 3-4. Keep: dataset, shared-account detection, fingerprint similarity, Overview + Network Explorer + Pattern + Early Warning pages. Drop: Upload page UI (keep the endpoint), optional radar charts, jitter calibration.

### 11.3 If you only have 2 days

Day 1: dataset + both engines, tested from the command line. Day 2: FastAPI + three pages (Overview, Network Explorer, Pattern/Early Warning combined) + evidence. Say plainly in the submission which features were not built. **Never trade away integration and testing for extra features.**

---

## 12. Testing and evaluation

### 12.1 Metric definitions (compute, never invent)

All metrics are **pair-level** over the 15 reported-case pairs in `ground_truth.csv`.

| Metric | Definition |
|---|---|
| Shared-account relationships found | predicted-connected pairs that are `expect_connected = Yes` |
| Shared-account false links | predicted-connected pairs with `expect_connected = No` |
| Similar pairs identified | predicted-similar pairs that are `expect_similar = Yes` |
| Unrelated pairs wrongly flagged | predicted-similar pairs with `expect_similar = No` |
| Missed pairs | expected but not predicted (both types) |
| Similarity margin | min(similar pair scores) minus max(dissimilar pair scores) |
| Anomaly separation | mean anomaly score of reported cases vs `NORM_*` clusters |
| Processing time | seconds to run discovery + fingerprinting + comparison (median of 5 runs) |

### 12.2 `evaluation/evaluate.py`

```python
import json
import statistics
import time
import pandas as pd

from backend.graph_engine import load_transactions
from backend.state import State

def evaluate():
    df = load_transactions("dataset/transactions.csv")
    gt = pd.read_csv("dataset/ground_truth.csv")

    times = []
    for _ in range(5):
        t0 = time.perf_counter()
        s = State(); s.load(df)
        times.append(time.perf_counter() - t0)

    pred_conn = {frozenset((c["case_a"], c["case_b"])) for c in s.graph_result["connections"]}
    pred_sim = {frozenset((p["case_a"], p["case_b"])) for p in s.pairs if p["is_similar"]}

    exp_conn = {frozenset((r.case_1, r.case_2)) for r in gt.itertuples() if r.expect_connected == "Yes"}
    exp_sim = {frozenset((r.case_1, r.case_2)) for r in gt.itertuples() if r.expect_similar == "Yes"}

    reported_scores = [s.anomaly.score(s.engine.fingerprints.loc[c].values) for c in s.reported]
    norm_ids = [c for c in s.engine.fingerprints.index if c.startswith("NORM_")]
    norm_scores = [s.anomaly.score(s.engine.fingerprints.loc[c].values) for c in norm_ids]

    result = {
        "n_transactions": len(df), "n_reported_cases": len(s.reported),
        "n_pairs_evaluated": len(gt),
        "connected_expected": len(exp_conn), "connected_found": len(pred_conn & exp_conn),
        "connected_false_links": len(pred_conn - exp_conn),
        "similar_expected": len(exp_sim), "similar_found": len(pred_sim & exp_sim),
        "similar_false_flags": len(pred_sim - exp_sim),
        "missed_connected": len(exp_conn - pred_conn), "missed_similar": len(exp_sim - pred_sim),
        "threshold": s.cal, "hub_accounts_ignored": s.graph_result["ignored_hub_accounts"],
        "mean_anomaly_reported": round(sum(reported_scores) / len(reported_scores), 3),
        "mean_anomaly_normal": round(sum(norm_scores) / len(norm_scores), 3),
        "processing_time_sec_median": round(statistics.median(times), 3),
    }
    with open("evaluation/results/metrics.json", "w") as f:
        json.dump(result, f, indent=2, default=str)
    print(json.dumps(result, indent=2, default=str))

if __name__ == "__main__":
    evaluate()
```

Run: `python -m evaluation.evaluate` (add `evaluation/__init__.py`). The team's results slide must quote numbers from this file.

### 12.3 Required test matrix

| Test | Expected |
|---|---|
| A-B, A-C, B-C connected | Yes, via B900 (A-B also G777) |
| D connected to A/B/C by accounts | No |
| D similar to A/B/C by behaviour | Yes |
| E (control) linked to anything | No |
| F (near-miss) linked to anything | No |
| A-F via hub U001 | Ignored |
| Wrong CSV upload | Clear 400 error |
| Simulated "ordinary payments" scenario | Low priority |
| Simulated fan-out scenario | High priority |
| Re-running the pipeline | Identical results (fixed seeds) |

### 12.4 Stress variants so you don't overclaim **[R1-FIX]**

Because you control the synthetic scenarios, a perfect score is expected. Add robustness checks and report them honestly:

1. **Noise:** regenerate Case D with amounts x 0.6-1.6 and gaps x 0.5-3. Record at what level similarity stops separating from controls.
2. **Near-miss sweep:** vary Case F's `speed` from 1 to 40 and plot similarity against speed. Report where it crosses the threshold.
3. **Ablation:** remove the intermediary-usage features (`n_passthrough`, `hop_depth`, `retention`) and report how the margin changes. This justifies adding them.
4. **Threshold sensitivity:** report how many false flags appear at threshold -0.05 and +0.05.

State plainly: *"Validated on controlled synthetic scenarios; real-world performance is unknown."*

---

## 13. Demo script

Total time about 4 minutes. Keep a recorded backup.

1. **Setup (10 s).** Dashboard open on Overview; point to the banner: leads for review, synthetic data, no blocking.
2. **Overview (30 s).** Totals and the ranked case list: "investigators see which cases to review first."
3. **Missing Link part 1, shared accounts (60 s).** Network Explorer, select A, B, C. Point at the red diamond B900: "A, B and C are different banks and different victims, but funds pass through the same account." Open the supporting transaction IDs. Mention the ignored hub account.
4. **Money Trail (45 s).** Case A: chronological table, the detected split and consolidation, path amounts.
5. **Missing Link part 2, pattern fingerprint (60 s).** Pattern page: A vs D similarity; "Shared accounts: 0" and the matching features. Then show Case E and Case F staying below the threshold.
6. **Early Warning (45 s).** Run the fan-out preset, show risk level, reasons and matched features; then the ordinary-payments preset showing Low.
7. **Close (15 s).** State the limitation: validated on synthetic scenarios; leads, not proof.

Keep this in `documentation/demo_script.md` with exact clicks.

---

## 14. Limitations to document honestly

- All results come from **synthetic** data designed by the team; real banking behaviour is more varied and noisy.
- Similarity thresholds are calibrated on a small number of cases; margins may not generalise.
- The risk score is a transparent heuristic, **not** a trained or validated predictive model.
- Shared-account detection depends on a hub-degree threshold that must be tuned per institution.
- A real cross-bank deployment requires data-sharing agreements, privacy controls, legal review and security hardening; none are implemented.
- Outputs are investigative leads and need human review; false positives and false negatives are possible.
- No integration with real payment systems; no blocking or enforcement actions by design.

---

## 15. Evidence to collect for the team-authored submission

Do not paste generated slides. Collect the raw evidence below; the team then writes and assembles the PPT/PDF itself.

**Screenshots (real, from your running app):** save in `evaluation/results/screenshots/` with names like `01_overview.png`.

1. Overview with ranked case list and banner
2. Network Explorer with shared intermediary highlighted
3. Connection explanation panel with supporting transaction IDs
4. Money Trail with split and path details
5. Pattern page: A vs D with 0 shared accounts
6. Pattern page: control/near-miss below threshold
7. Early Warning: High result with reasons
8. Early Warning: Low result
9. Upload page with success and an error case
10. Terminal output of `pytest` and `evaluate.py`

**Numbers (from `metrics.json`):** cases tested, connected pairs found vs expected, similar pairs found vs expected, false links/flags, margin, anomaly separation, processing time, stress-test results.

**Diagrams (team-drawn):** architecture (data -> loader -> graph engine + fingerprint engine -> API -> dashboard), data schema, the Missing Link concept.

**Slide-to-evidence map (what each section of your own deck should draw on):**

| Deck section | Evidence source | Owner |
|---|---|---|
| Title, team | your details | M4 |
| Problem and motivation | your Round 1 text, updated | M1 |
| Solution and innovation | Missing Link concept | All |
| Architecture | `architecture.md` diagram | M4 |
| Dataset | `dataset_description.md`, validator output | M1 |
| Cross-case discovery | screenshots 2-3, graph output | M2 |
| Pattern fingerprinting | screenshots 5-6, features table | M3 |
| Money trail + early warning | screenshots 4, 7-8 | M2 + M3 |
| Testing, results, limitations | `metrics.json`, stress tests, Section 14 | All |
| Impact, future scope | your own analysis | M4 |

Before submitting, verify the Google Drive sharing permissions.

---

## 16. Master checklist

### Member 1: Data
- [ ] Generator runs and is reproducible (seed 42)
- [ ] Three banks, `sender_bank` and `receiver_bank` columns
- [ ] CASE_A/B/C connected through B900; A-B also share G777
- [ ] CASE_D similar behaviour, zero shared accounts
- [ ] CASE_E control and CASE_F near-miss
- [ ] Hub U001 trap present
- [ ] 40 normal clusters and background traffic
- [ ] Public dataset baseline loaded and licence cited (or justification written)
- [ ] `ground_truth.csv` with 15 pairs
- [ ] Validator passes; dataset documentation written

### Member 2: Graph
- [ ] Directed timestamped graph built with NetworkX
- [ ] Shared accounts found, roles classified
- [ ] Hub filter works and reports ignored accounts
- [ ] Case groups computed
- [ ] Splitting, consolidation and time-respecting paths detected
- [ ] JSON evidence exported; `test_graph.py` passes

### Member 3: AI
- [ ] 15 features including intermediary-usage features
- [ ] Scaler fit on reference pool
- [ ] Similarity engine with explanations
- [ ] Threshold calibrated; margin reported
- [ ] Isolation Forest trained on normal clusters
- [ ] Risk score heuristic documented; neutral level wording
- [ ] Early-warning presets work; `test_patterns.py` passes

### Member 4: Product
- [ ] FastAPI endpoints incl. `/upload-transactions` and ranked `/cases`
- [ ] Disclaimer banner on every page
- [ ] Six pages built; legend on graph
- [ ] Offline demo, `run_demo.sh`, backup recording
- [ ] Integration test passes
- [ ] Screenshots captured; demo script and architecture docs written

### Team
- [ ] All modules tested together; end-to-end demo rehearsed
- [ ] `evaluate.py` run; stress tests recorded
- [ ] Limitations documented
- [ ] Evidence pack complete
- [ ] PPT/PDF written and assembled by the team
- [ ] Google Drive sharing verified

---

**Time check:** if your Round 2 deadline is shorter than five days, use the 3-day or 2-day cuts in Section 11 and tell the team which features are intentionally left out.
