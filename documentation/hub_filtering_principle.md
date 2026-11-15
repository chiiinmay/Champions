# Architectural Decision: Hub Filtering in Pattern Fingerprinting & Graph Analysis

## 1. Principle & Threat Model

In financial crime analysis across multiple institutions, accounts fall into two categories:
1. **Participating Entities:** Victims, mule accounts, intermediaries, and cashout accounts acting as elements of a money laundering syndicate.
2. **Ambient Infrastructure / Hub Accounts:** High-degree accounts belonging to utility providers (electricity, telecom), government tax authorities, municipal utilities, and major retail payment processors (e.g. account `AU001` with total degree 43 in the synthetic benchmark).

### Shared Hub Detection Across Phases:
Phase 2 (`backend/cross_case_detection.py`) and Phase 3 (`backend/feature_extraction.py`, `backend/fingerprint_engine.py`, `backend/risk_assessment.py`) share a single unified hub-degree threshold (`HUB_DEGREE_THRESHOLD = 25`) and shared detection logic (`get_hub_accounts`):
- Any account whose total degree across all transactions (including ambient background traffic) exceeds 25 is identified as a hub.
- In Phase 2, hubs are excluded from cross-case link discovery to prevent false co-conspirator connections.
- In Phase 3, transactions touching hub accounts are excluded prior to feature extraction when `filter_hubs=True`.

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

---

## 3. Decision Timeline and Limitations

### 3.1 Decision Timeline:
- The default flag `filter_hubs = True` was **not** an a priori theoretical assumption; it was selected **after empirically evaluating both configurations**.
- When hub filtering was evaluated in the OFF state, the similarity between `CASE_A` and `CASE_D` dropped to `0.601` because a single ₹1,500 bill payment from `G777` to utility hub `AU001` turned `G777` into a pass-through node and artificially increased hop depth.
- In the OFF state, near-miss `CASE_F` exhibited a similarity of `0.672` to `CASE_D`, exceeding the similar pair similarity and yielding a **negative calibration margin of -0.072**.
- Enabling hub filtering eliminated the ambient `AU001` noise, restoring `CASE_A`'s true layered topology and yielding a positive separation margin of `+0.238`. Both numbers are preserved and reported honestly.

### 3.2 Limitations & Dependencies:
1. **Critical Sensitivity to Hub Threshold:**
   - The engine's success depends directly on the chosen hub threshold (`HUB_DEGREE_THRESHOLD`).
   - If the threshold is set too low (e.g. `15`), high-volume criminal mules (such as `B900` with degree 16) are falsely filtered out as hubs, stripping the fraud cases of their actual mule transfers and collapsing the margin to `-0.237` with 3 false negatives.
   - If the threshold is set too high (e.g. `50`), the utility hub `AU001` (degree 43) is not filtered, reproducing the negative margin of `-0.072`.
   - The threshold must be tuned and validated empirically for each deployment environment.
2. **Negative Margin Without Hub Filtering:**
   - Without hub filtering, the engine **fails to achieve positive class separation** on this benchmark (`margin = -0.072`).
   - Users and investigators must be aware that raw, unfiltered transaction data containing incidental utility expenditures will distort pattern fingerprints.
3. **Synthetic Validation Scope:**
   - All results reflect the synthetic benchmark design. In real-world banking data, merchant and utility transactions are substantially more varied, and mule accounts may make multiple everyday purchases that cannot be filtered solely by degree.
