
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from backend.graph_engine import load_transactions
from backend.cross_case_detection import discover_connections

DATASET_PATH = ROOT / "dataset" / "transactions.csv"
OUTPUT_PATH = ROOT / "evaluation" / "results" / "graph_output.json"


def main():
    df = load_transactions(DATASET_PATH)
    results = discover_connections(df)

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)

    with OUTPUT_PATH.open("w", encoding="utf-8") as f:
        json.dump(results, f, indent=2, sort_keys=True)
        f.write("\n")

    print(f"Exported: {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
