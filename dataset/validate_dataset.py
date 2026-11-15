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
