import numpy as np
from sklearn.ensemble import IsolationForest


class AnomalyScorer:
    """Trains an Isolation Forest exclusively on normal reference clusters (NORM_*),
    establishing an empirical baseline of ordinary transaction patterns.
    Reported cases are scored relative to this distribution.
    """

    def __init__(self, engine):
        normal_ids = [c for c in engine.fingerprints.index if c.startswith("NORM_")]
        if not normal_ids:
            raise ValueError("No NORM_* reference clusters found to train IsolationForest.")
        X = engine.fingerprints.loc[normal_ids].values
        self.model = IsolationForest(n_estimators=200, contamination="auto", random_state=42).fit(X)
        raw = -self.model.score_samples(engine.fingerprints.values)  # Higher = more anomalous
        self._lo = float(raw.min())
        self._hi = float(raw.max())

    def score(self, z: np.ndarray) -> float:
        """Computes a normalized anomaly score in [0, 1] relative to the reference population."""
        raw = -self.model.score_samples(z.reshape(1, -1))[0]
        denom = self._hi - self._lo + 1e-9
        return float(np.clip((raw - self._lo) / denom, 0.0, 1.0))
