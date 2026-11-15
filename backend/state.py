"""
backend/state.py  –  In-memory application state (Phase 4a).

All state lives here; nothing is persisted. upload-transactions only mutates
this object, never touches dataset/transactions.csv.
"""
import pandas as pd

from backend.graph_engine import load_transactions
from backend.cross_case_detection import discover_connections
from backend.fingerprint_engine import FingerprintEngine
from backend.anomaly_detection import AnomalyScorer
from backend.similarity_engine import calibrate_threshold, compare_all
from backend.risk_assessment import assess_case

# Full disclaimer text – reused by every endpoint that returns findings.
DISCLAIMER = (
    "SHADOWNET outputs are investigative leads for human review, not proof of "
    "criminal activity. The system does not block payments or determine guilt. "
    "All data shown is synthetic."
)


class AppState:
    """Holds the live dataset and all derived analytical objects.

    Call .load(df) to (re)initialise from any DataFrame that passes the
    load_transactions schema check.  load() is idempotent: calling it again
    simply replaces the previous state.
    """

    def __init__(self):
        self.df: pd.DataFrame = pd.DataFrame()
        self.graph_result: dict = {}
        self.engine: FingerprintEngine | None = None
        self.anomaly: AnomalyScorer | None = None
        self.reported: list[str] = []
        self.cal: dict = {"threshold": 0.80}
        self.pairs: list[dict] = []
        self.case_risk: dict[str, dict] = {}
        self.escalation_rule: bool = False

    def load(self, df: pd.DataFrame,
             ground_truth_path: str = "dataset/ground_truth.csv",
             escalation_rule: bool = False) -> None:
        """(Re)build all analytical objects from df.

        Never writes to disk.  is_synthetic_suspicious is not used as a model
        input anywhere in this method.
        """
        self.escalation_rule = escalation_rule
        self.df = df
        self.graph_result = discover_connections(df)

        self.engine = FingerprintEngine(df)
        self.anomaly = AnomalyScorer(self.engine)

        self.reported = sorted(
            c for c in df.case_id.unique() if c.startswith("CASE_")
        )

        try:
            gt = pd.read_csv(ground_truth_path)
            self.cal = calibrate_threshold(self.engine, gt)
        except Exception:
            self.cal = {"threshold": 0.80}

        self.pairs = compare_all(self.engine, self.reported, self.cal["threshold"])

        self.case_risk = {}
        for cid in self.reported:
            others = [c for c in self.reported if c != cid]
            self.case_risk[cid] = assess_case(
                df[df.case_id == cid],
                self.engine,
                self.anomaly,
                others,
                self.cal["threshold"],
                existing_df=df[~df.case_id.eq(cid)],
                escalation_rule=self.escalation_rule,
            )


# Single shared instance imported by main.py
state = AppState()
