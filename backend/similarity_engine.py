from itertools import combinations
import numpy as np

from backend.feature_extraction import FEATURES


def similarity(za: np.ndarray, zb: np.ndarray) -> float:
    """Combined similarity metric bounded in [0, 1].
    
    Harmonizes direction/shape (cosine similarity) and magnitude/distance (inverse euclidean distance).
    """
    norm_a = np.linalg.norm(za)
    norm_b = np.linalg.norm(zb)
    cos = float(np.dot(za, zb) / (norm_a * norm_b + 1e-9))
    dist = float(np.linalg.norm(za - zb)) / np.sqrt(len(za))
    return 0.5 * ((cos + 1) / 2) + 0.5 * (1 / (1 + dist))


def matching_features(za, zb, raw_a, raw_b, tol=0.5, top=5) -> list[dict]:
    """Identifies the features where standardized behavioral profiles are closest."""
    diffs = [(abs(za[i] - zb[i]), FEATURES[i]) for i in range(len(FEATURES))]
    diffs.sort(key=lambda x: x[0])
    return [
        {
            "feature": f,
            "a": round(float(raw_a[f]), 3),
            "b": round(float(raw_b[f]), 3)
        }
        for d, f in diffs[:top] if d <= tol
    ]


def compare_all(engine, reported_ids, threshold) -> list[dict]:
    """Pairwise comparison of all specified reported cases."""
    out = []
    for a, b in combinations(reported_ids, 2):
        za = engine.fingerprints.loc[a].values
        zb = engine.fingerprints.loc[b].values
        s = similarity(za, zb)
        out.append({
            "case_a": a,
            "case_b": b,
            "similarity": round(s, 3),
            "is_similar": bool(s >= threshold),
            "matching_features": matching_features(
                za, zb, engine.features.loc[a], engine.features.loc[b]
            )
        })
    return out


def calibrate_threshold(engine, ground_truth) -> dict:
    """Calibrates similarity threshold in the boundary between lowest expected-similar
    pair and highest expected-dissimilar pair. Computes the separation margin.
    """
    sims, dis = [], []
    for r in ground_truth.itertuples():
        s = similarity(
            engine.fingerprints.loc[r.case_1].values,
            engine.fingerprints.loc[r.case_2].values
        )
        if r.expect_similar == "Yes":
            sims.append(s)
        else:
            dis.append(s)

    lo, hi = float(min(sims)), float(max(dis))
    threshold = (lo + hi) / 2
    margin = lo - hi

    return {
        "threshold": round(threshold, 3),
        "min_similar": round(lo, 3),
        "max_dissimilar": round(hi, 3),
        "margin": round(margin, 3)
    }
