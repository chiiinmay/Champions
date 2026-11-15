# SHADOWNET: Dataset Description & Validation Report

## 1. Overview & Disclaimer

> **Investigative leads only:** All transactions in this dataset are generated synthetically. They do not represent real individuals or live banking records. The system provides investigative leads for human review, not proof of criminal activity.

## 2. Multi-Bank Architecture & Data Contract

Transactions simulate activity across three distinct financial institutions:
- **Bank Alpha** (Account prefix `A`)
- **Bank Beta** (Account prefix `B`)
- **Bank Gamma** (Account prefix `G`)

### 2.1 `transactions.csv` Schema

| Column | Type | Example | Description |
|---|---|---|---|
| `transaction_id` | str | `TX00001` | Unique transaction identifier |
| `case_id` | str | `CASE_A` | Associated case (`CASE_*` = reported fraud, `NORM_*` = normal cluster, `BACKGROUND` = ambient noise) |
| `sender_bank` | str | `Bank Alpha` | Originating bank institution |
| `receiver_bank` | str | `Bank Beta` | Destination bank institution |
| `sender_account` | str | `A101` | Source account identifier |
| `receiver_account` | str | `B900` | Destination account identifier |
| `amount` | float | `20000.00` | Transfer value in INR (₹) |
| `timestamp` | datetime | `2026-11-01 09:00:00` | ISO format timestamp |
| `transaction_type` | str | `Transfer` | Type of transfer (e.g., Transfer, Payment, Bill Payment) |
| `is_synthetic_suspicious` | Yes/No | `Yes` | Simulation label (internal truth only; excluded from model inputs) |
| `source` | str | `synthetic` | Clear labelling (`synthetic`, `synthetic_paysim_style`, or `public_paysim`) |

### 2.2 `cases.csv` Schema
- `case_id`: Unique case ID
- `case_type`: `reported_fraud` or `normal_cluster`
- `n_transactions`: Transaction count
- `start_time`, `end_time`: Bounding timestamps

### 2.3 `ground_truth.csv` Schema
Provides pairwise relationship labels across all pairs of reported cases (`CASE_A` through `CASE_F`):
- `case_1`, `case_2`: Pair endpoints
- `relation`: `shared_account`, `similar_pattern`, `unrelated`, `hub_only`, `near_miss`
- `expect_connected`: `Yes` or `No`
- `expect_similar`: `Yes` or `No`
- `notes`: Specific rationale

---

## 3. Case Scenarios & Ground Truth Design

1. **CASE_A, CASE_B, CASE_C (Connected via Intermediary B900):**
   - Pattern P1 layered mule flow.
   - All three cases share mule intermediary `B900`.
   - `CASE_A` and `CASE_B` also share cash-out beneficiary `G777`.
   - `CASE_C` routes to cash-out beneficiary `G888`.
   - Expected: `expect_connected = Yes`, `expect_similar = Yes`.

2. **CASE_D (The "Missing Link" - Disconnected but Similar):**
   - Pattern P1 layered mule flow with completely disjoint accounts.
   - Zero shared accounts with `CASE_A`, `CASE_B`, `CASE_C`.
   - Expected: `expect_connected = No`, `expect_similar = Yes`.

3. **CASE_E (Control):**
   - Single large transfer held for 2 days followed by onward transfer.
   - Disjoint accounts, different timing and topology.
   - Expected: `expect_connected = No`, `expect_similar = No`.

4. **CASE_F (Near-Miss & Hub Trap):**
   - Layered structure but slow execution (hours between steps).
   - Only 2 second-layer accounts.
   - Directs payment to utility/hub account `AU001`.
   - Expected: `expect_connected = No` (hub `AU001` filtered), `expect_similar = No` (timing differs).

5. **NORM_00..39 (Reference Population):**
   - 40 small normal clusters (1-2 hops, 2-5 transfers, multi-hour/day gaps).
   - Serves as reference population for feature scaling and Isolation Forest anomaly baseline.

6. **BACKGROUND Traffic & Hub `AU001`:**
   - 400 random ordinary transfers among 150 background accounts.
   - Hub account `AU001` receives 40+ bill payments, establishing high graph degree for the hub filter.

---

## 4. Synthetic PaySim-Style Baseline & Real Public Data Integration

### 4.1 Bundled Baseline Sample: `synthetic_baseline_sample.csv`
- **Honest Disclosure:** The bundled file `dataset/synthetic_baseline_sample.csv` is **synthetic mock data** generated locally to mirror the exact columns and schema of the Kaggle PaySim dataset for offline testing and reproducibility. It is **not** real PaySim research data (amounts and balances are generated programmatically, and `isFraud` is set to 0).
- When loaded via `dataset/load_public_baseline.py`, its records are explicitly labelled with `source = "synthetic_paysim_style"` to ensure complete transparency.

### 4.2 Loading Real Public PaySim Data (TODO)
To integrate real public data from the PaySim benchmark:
```text
TODO: Real Public PaySim Data Integration
1. Download the official PaySim dataset from Kaggle:
   https://www.kaggle.com/datasets/ealaxi/paysim1
   (Licence: CC BY-SA 4.0; Authors: Lopez-Rojas, Elmir, Axelsson)
2. Place the uncompressed CSV at: dataset/real_paysim.csv
3. In dataset/load_public_baseline.py, call:
   load_paysim("dataset/real_paysim.csv", n=3000, is_real_public=True)
   This will sample rows and tag them with source="public_paysim".
```
