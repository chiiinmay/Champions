import pandas as pd

from backend.cross_case_detection import HUB_DEGREE_THRESHOLD
from backend.feature_extraction import case_features
from backend.similarity_engine import matching_features, similarity

DISCLAIMER = "Investigative lead only; not proof of criminal activity."
MODERATE_SIMILARITY_THRESHOLD = 0.45


def level(score: float) -> str:
    """Classifies risk score into standardized neutral priority wording."""
    if score >= 0.65:
        return "High priority for review"
    if score >= 0.35:
        return "Medium priority for review"
    return "Low priority for review"


def assess_case(case_df: pd.DataFrame, engine, anomaly, known_ids, threshold,
                existing_df=None, hub_threshold: int = HUB_DEGREE_THRESHOLD,
                escalation_rule: bool = False) -> dict:
    """Calculates explainable priority-for-review assessment based on:
    - Direct connections (shared accounts, ignoring hubs) [40%]
    - Behavioral pattern similarity to known fraud cases [35%]
    - Anomaly score relative to normal reference clusters [25%]

    Optional escalation rule (default off, behind config flag):
    Promotes risk_level to 'High priority for review' if the case matches at least
    two known reported cases above the calibrated similarity threshold and has
    an anomaly score above 0.8.
    """
    hub_accounts = engine.hub_accounts if getattr(engine, "filter_hubs", True) else None
    feats = case_features(case_df, hub_accounts=hub_accounts)
    z = engine.fingerprint_of(feats)

    sims = sorted(
        ((similarity(z, engine.fingerprints.loc[k].values), k) for k in known_ids),
        reverse=True
    )
    best_sim, best_id = sims[0]
    a_score = anomaly.score(z)

    # Direct connection: accounts shared with known reported cases (hubs ignored)
    shared = 0
    if existing_df is not None:
        known = existing_df[existing_df.case_id.isin(known_ids)]
        # pd.concat used instead of deprecated Series.append
        deg = pd.concat([existing_df.sender_account, existing_df.receiver_account]).value_counts()
        mine = set(case_df.sender_account) | set(case_df.receiver_account)
        theirs = set(known.sender_account) | set(known.receiver_account)
        shared = len([a for a in (mine & theirs) if deg.get(a, 0) <= hub_threshold])

    connection = min(1.0, shared / 2)
    score = 0.40 * connection + 0.35 * best_sim + 0.25 * a_score

    # Check escalation rule: similarity to >= 2 known cases > threshold AND anomaly > 0.8
    similar_to_known_count = sum(1 for s, k in sims if s > threshold)
    escalated = False
    if escalation_rule and similar_to_known_count >= 2 and a_score > 0.8:
        escalated = True
        risk_level = "High priority for review"
    else:
        risk_level = level(score)

    matched = matching_features(
        z, engine.fingerprints.loc[best_id].values,
        feats, engine.features.loc[best_id]
    )
    
    reasons = []
    if shared > 0:
        reasons.append(f"Shares {shared} non-hub account(s) with previously reported cases.")
    if best_sim >= threshold:
        reasons.append(f"Behaviour closely resembles {best_id} (similarity {best_sim:.2f}).")
    elif best_sim >= MODERATE_SIMILARITY_THRESHOLD:
        reasons.append(f"Behaviour moderately resembles {best_id} (similarity {best_sim:.2f}).")
    if feats["split_ratio"] >= 3:
        reasons.append(f"Funds fan out to {feats['split_ratio']} accounts from a single account.")
    # Rapid succession: require at least two transactions and timing feature supporting it
    if feats["n_tx"] >= 2 and feats["log_median_gap_min"] < 3.5:
        reasons.append("Transfers occur in rapid succession.")
    if a_score > 0.6:
        reasons.append("Behaviour is unusual compared with the normal reference population.")
    if escalated:
        reasons.append(
            f"Escalated to High priority: highly anomalous pattern (anomaly {a_score:.2f}) "
            f"matches {similar_to_known_count} known reported cases above similarity threshold."
        )
    if not reasons:
        if score >= 0.35:
            reasons.append(f"Assessed as {risk_level.lower()} based on overall composite risk.")
        else:
            reasons.append("No strong similarity or connection to known cases was found.")

    return {
        "risk_score": round(score, 3),
        "risk_level": risk_level,
        "escalated": escalated,
        "components": {
            "connection": round(connection, 2),
            "pattern_similarity": round(best_sim, 2),
            "anomaly": round(a_score, 2)
        },
        "closest_known_cases": [{"case_id": k, "similarity": round(s, 2)} for s, k in sims[:3]],
        "matched_features": [m["feature"] for m in matched],
        "reasons": reasons,
        "disclaimer": DISCLAIMER
    }
