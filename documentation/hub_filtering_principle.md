# Architectural Decision: Hub Filtering in Pattern Fingerprinting & Graph Analysis

## 1. Principle & Threat Model

In financial crime analysis across multiple institutions, accounts fall into two categories:
1. **Participating Entities:** Victims, mule accounts, intermediaries, and cashout accounts acting as elements of a money laundering syndicate.
2. **Ambient Infrastructure / Hub Accounts:** High-degree accounts belonging to utility providers (electricity, telecom), government tax authorities, municipal utilities, and major retail payment processors (e.g. account `AU001` with degree 43 in the synthetic benchmark).

### Why Hub Filtering is Mandatory on Principle:
- **In Graph Intelligence (Phase 2):** If high-degree accounts are retained, legitimate ambient payments (such as thousands of citizens paying an electric bill) create massive false-positive edges between completely unrelated victims and fraud cases.
- **In Pattern Fingerprinting (Phase 3):** Fraud rings frequently make incidental or operational bill payments from mule or cash-out accounts (e.g. `CASE_A` pays ₹1,500 to utility hub `AU001`). If this transaction is treated as part of the core laundering chain:
  - The cash-out account (`G777`) is falsely reclassified as a pass-through node rather than a terminal cash-out account.
  - The graph hop-depth artificially increases by +1.
  - The layer distribution (`layer_0..3`) shifts, corrupting the case's behavioral fingerprint.

Therefore, **on first principles of fraud intelligence preprocessing, hub filtering (`filter_hubs=True`) must be enabled by default** across both graph connection discovery and topological feature extraction.

---

## 2. Empirical Comparison: Hub Filtering OFF vs ON

| Metric | Hub Filtering OFF (`filter_hubs=False`) | Hub Filtering ON (`filter_hubs=True` - Default) |
|---|---|---|
| **Underlying Principle** | Raw transaction parsing with no ambient noise removal | Principle-based noise elimination of high-degree utility nodes |
| **CASE_A vs CASE_D Similarity** | 0.601 | **0.979** |
| **Min Similar Pair (`min_similar`)** | 0.600 (`CASE_A` - `CASE_C`) | **0.907** (`CASE_B` - `CASE_C`) |
| **Max Dissimilar Pair (`max_dissimilar`)** | 0.672 (`CASE_D` - `CASE_F`) | **0.669** (`CASE_E` - `CASE_F`) |
| **Separation Margin** | **-0.072** (Negative / inverted) | **+0.238** (Strictly positive separation) |
| **Calibrated Threshold** | 0.636 | **0.788** |
| **Mean Anomaly (CASE_*)** | 0.824 | **0.796** |
| **Mean Anomaly (NORM_*)** | 0.319 | **0.319** |

### Analysis of the Margin Shift:
- When hub filtering is **OFF**, the incidental payment `G777 -> AU001` in `CASE_A` alters its feature vector so significantly that its similarity to `CASE_D` drops from 0.979 down to 0.601. Because near-miss `CASE_F` has a similarity of 0.672 to `CASE_D`, the dissimilar score exceeds the similar score, collapsing the margin to `-0.072`.
- When hub filtering is **ON** (the default), `AU001` transactions are appropriately filtered as infrastructure noise. `CASE_A`, `CASE_B`, `CASE_C`, and `CASE_D` all demonstrate strong mutual similarity (0.907 to 0.980), cleanly separating from controls and near-misses with a margin of **+0.238**.
