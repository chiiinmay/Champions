import numpy as np
import pandas as pd
from sklearn.preprocessing import StandardScaler

from backend.feature_extraction import FEATURES, all_case_features


class FingerprintEngine:
    """Extracts features across the reference pool (NORM_* clusters and reported cases),
    standardizes them with StandardScaler, and computes behavioral fingerprints.
    """

    def __init__(self, df: pd.DataFrame, filter_hubs: bool = True, hub_threshold: int = 25):
        self.filter_hubs = filter_hubs
        self.hub_threshold = hub_threshold
        
        # Identify hub accounts across all transactions if filter_hubs is enabled
        self.hub_accounts = None
        if self.filter_hubs:
            total_deg = pd.concat([df.sender_account, df.receiver_account]).value_counts()
            self.hub_accounts = set(total_deg[total_deg > self.hub_threshold].index)

        self.features = all_case_features(df, filter_hubs=self.filter_hubs, hub_threshold=self.hub_threshold)
        self.scaler = StandardScaler().fit(self.features.values)
        z = self.scaler.transform(self.features.values)
        self.fingerprints = pd.DataFrame(z, index=self.features.index, columns=FEATURES)

    def fingerprint_of(self, feature_row: dict) -> np.ndarray:
        """Transforms a single feature dictionary into a standardized fingerprint vector."""
        x = np.array([[feature_row[f] for f in FEATURES]])
        return self.scaler.transform(x)[0]
