import hashlib
from pathlib import Path
import pandas as pd

BANKS = ["Bank Alpha", "Bank Beta", "Bank Gamma"]


def bank_of(account: str) -> str:
    """Deterministically maps an account string to one of the 3 simulated banks."""
    return BANKS[int(hashlib.md5(account.encode()).hexdigest(), 16) % 3]


def load_paysim(path, n=3000, seed=42, is_real_public=False):
    """Loads a PaySim-formatted dataset.
    
    NOTE: The bundled baseline sample (synthetic_baseline_sample.csv) is synthetic data
    generated to match PaySim's column structure for offline testing and reproducibility.
    It is NOT real PaySim research data.
    
    Source label is set to 'synthetic_paysim_style' to reflect this honestly.
    """
    raw = pd.read_csv(path)
    filtered = raw[raw["type"].isin(["TRANSFER", "PAYMENT"])]
    sample_size = min(n, len(filtered))
    sampled = filtered.sample(sample_size, random_state=seed) if sample_size > 0 else filtered
    base = pd.Timestamp("2026-11-01 00:00:00")
    source_label = "public_paysim" if is_real_public else "synthetic_paysim_style"
    
    out = pd.DataFrame({
        "transaction_id": [f"PUB{i:05d}" for i in range(len(sampled))],
        "case_id": "BACKGROUND",
        "sender_bank": sampled["nameOrig"].map(bank_of).values,
        "receiver_bank": sampled["nameDest"].map(bank_of).values,
        "sender_account": sampled["nameOrig"].values,
        "receiver_account": sampled["nameDest"].values,
        "amount": sampled["amount"].clip(lower=1).values,
        "timestamp": (base + pd.to_timedelta(sampled["step"].values, unit="h")),
        "transaction_type": sampled["type"].str.title().values,
        "is_synthetic_suspicious": "No",
        "source": source_label,
    })
    return out


# ==============================================================================
# TODO: Real Public Dataset Loading Instructions
# To load a real downloaded PaySim dataset (e.g. from Kaggle - PS_201743927130_148014447.csv):
# 1. Download the real PaySim dataset from Kaggle:
#    https://www.kaggle.com/datasets/ealaxi/paysim1
# 2. Place the uncompressed CSV at: dataset/real_paysim.csv
# 3. Call load_paysim("dataset/real_paysim.csv", n=3000, is_real_public=True)
#    This will sample 3000 rows and label them with source="public_paysim".
# ==============================================================================


def create_sample_paysim(path="dataset/synthetic_baseline_sample.csv", n=500, seed=42):
    """Creates a synthetic sample matching PaySim schema for offline development/testing.
    
    This is synthetic data, NOT real PaySim data.
    """
    import numpy as np
    np.random.seed(seed)
    steps = np.random.randint(1, 100, size=n)
    types = np.random.choice(["TRANSFER", "PAYMENT"], size=n, p=[0.4, 0.6])
    amounts = np.round(np.random.lognormal(mean=7.5, sigma=1.0, size=n), 2)
    origs = [f"C{np.random.randint(1000000, 9999999)}" for _ in range(n)]
    dests = [f"M{np.random.randint(1000000, 9999999)}" for _ in range(n)]
    
    df = pd.DataFrame({
        "step": steps,
        "type": types,
        "amount": amounts,
        "nameOrig": origs,
        "oldbalanceOrg": amounts * 1.5,
        "newbalanceOrig": amounts * 0.5,
        "nameDest": dests,
        "oldbalanceDest": 0.0,
        "newbalanceDest": amounts,
        "isFraud": 0,
        "isFlaggedFraud": 0
    })
    out_path = Path(path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(out_path, index=False)
    return df


if __name__ == "__main__":
    p = Path(__file__).parent / "synthetic_baseline_sample.csv"
    if not p.exists():
        create_sample_paysim(p)
        print(f"Created synthetic PaySim-style sample at {p}")
    baseline_df = load_paysim(p, is_real_public=False)
    print(f"Loaded {len(baseline_df)} records from {p.name} (source='{baseline_df['source'].iloc[0]}').")
