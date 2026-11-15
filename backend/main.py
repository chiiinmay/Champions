"""
backend/main.py  –  FastAPI application (Phase 4a, Sections 10.2–10.3, 10.7).

Endpoints
---------
GET  /health
GET  /overview
GET  /cases                      ranked by risk_score descending
GET  /transactions               optional ?case_id= filter
GET  /graph                      ?cases=CASE_A,CASE_B  → Cytoscape JSON
POST /upload-transactions        CSV upload; validates schema; never writes to disk
POST /discover-connections
POST /compare-patterns
GET  /money-trail/{case_id}
POST /simulate-risk

Guardrails (all checked here)
------------------------------
* Every response that shows findings includes DISCLAIMER text.
* "priority for review" wording only – no verdict labels.
* No block/freeze endpoint.
* /upload-transactions returns HTTP 400 for wrong schema.
* /upload-transactions only changes in-memory state; transactions.csv is NEVER touched.
* is_synthetic_suspicious is NOT used as a model input anywhere.
* CORS only for http://localhost:5173.
"""
import io

import pandas as pd
from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from backend.graph_engine import load_transactions, build_graph, graph_to_cytoscape
from backend.money_flow import money_trail
from backend.risk_assessment import assess_case
from backend.state import state, DISCLAIMER

# ---------------------------------------------------------------------------
# Application
# ---------------------------------------------------------------------------

app = FastAPI(
    title="SHADOWNET API",
    description=(
        "AI-powered cross-case financial fraud intelligence. "
        "Outputs are investigative leads for human review, not proof of criminal activity. "
        "No payment blocking or guilt determination. All data synthetic."
    ),
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_methods=["*"],
    allow_headers=["*"],
    allow_credentials=False,
)

# ---------------------------------------------------------------------------
# Startup
# ---------------------------------------------------------------------------

@app.on_event("startup")
def startup() -> None:
    """Load the bundled synthetic dataset into memory on server start."""
    state.load(load_transactions("dataset/transactions.csv"))


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------

@app.get("/health")
def health() -> dict:
    """Liveness probe – returns immediately without touching state."""
    return {"status": "ok"}


@app.get("/overview")
def overview() -> dict:
    """High-level summary counts plus the mandatory disclaimer."""
    df = state.df
    return {
        "cases": len(state.reported),
        "accounts": int(
            pd.concat([df.sender_account, df.receiver_account]).nunique()
        ),
        "transactions": len(df),
        "relationships": len(state.graph_result.get("connections", [])),
        "similar_pairs": sum(p["is_similar"] for p in state.pairs),
        "disclaimer": DISCLAIMER,
    }


@app.get("/cases")
def cases() -> list:
    """Reported cases ranked by risk_score descending (priority for review).

    Each row includes the full risk assessment and the disclaimer.
    No verdict labels are used; wording is 'priority for review'.
    """
    rows = [
        {"case_id": c, **state.case_risk[c], "disclaimer": DISCLAIMER}
        for c in state.reported
    ]
    return sorted(rows, key=lambda r: r["risk_score"], reverse=True)


@app.get("/transactions")
def transactions(case_id: str | None = None) -> list:
    """Return transactions, optionally filtered by case_id."""
    d = state.df if case_id is None else state.df[state.df.case_id == case_id]
    # timestamps must be serialisable
    return d.assign(timestamp=d.timestamp.astype(str)).to_dict("records")


@app.get("/graph")
def graph(cases: str) -> dict:
    """Cytoscape-compatible node/edge JSON for the requested case IDs.

    Pass a comma-separated list: ?cases=CASE_A,CASE_B
    Shared accounts (excluding hubs) are highlighted.
    """
    ids = [c.strip() for c in cases.split(",") if c.strip()]
    G = build_graph(state.df, ids)
    shared = {
        s["account"]
        for c in state.graph_result.get("connections", [])
        if c["case_a"] in ids and c["case_b"] in ids
        for s in c["shared_accounts"]
    }
    return graph_to_cytoscape(G, shared)


@app.post("/upload-transactions")
async def upload(file: UploadFile = File(...)) -> dict:
    """Upload a CSV, validate its schema, and reload in-memory state.

    Returns HTTP 400 with a clear message if the schema is wrong.
    NEVER writes to dataset/transactions.csv or any other file on disk.
    is_synthetic_suspicious is validated as a column but never used as a model
    input (see state.load → assess_case → feature_extraction).
    """
    raw = await file.read()
    try:
        df = load_transactions(io.BytesIO(raw))
    except Exception as exc:
        raise HTTPException(
            status_code=400,
            detail=(
                f"Invalid file: {exc}. "
                "Required columns: transaction_id, case_id, sender_bank, "
                "receiver_bank, sender_account, receiver_account, amount, "
                "timestamp, transaction_type, is_synthetic_suspicious, source."
            ),
        )
    state.load(df)
    return {
        "status": "loaded",
        "transactions": len(df),
        "cases": len(state.reported),
        "disclaimer": DISCLAIMER,
    }


@app.post("/discover-connections")
def discover() -> dict:
    """Return shared-account connections between reported cases.

    Result includes disclaimer.  Hub accounts are listed under
    ignored_hub_accounts – they are NOT used as links.
    """
    return {**state.graph_result, "disclaimer": DISCLAIMER}


@app.post("/compare-patterns")
def compare() -> dict:
    """Return pairwise behavioural similarity for all reported-case pairs.

    Includes calibrated threshold and disclaimer.  Similarity is based on
    structural/timing features; is_synthetic_suspicious is not a feature.
    """
    return {
        "pairs": state.pairs,
        "threshold": state.cal["threshold"],
        "disclaimer": DISCLAIMER,
    }


@app.get("/money-trail/{case_id}")
def trail(case_id: str) -> dict:
    """Reconstruct the chronological money trail for a known case.

    Returns HTTP 404 for an unknown case_id.
    """
    d = state.df[state.df.case_id == case_id]
    if d.empty:
        raise HTTPException(status_code=404, detail=f"Unknown case: {case_id}")
    return {**money_trail(d), "disclaimer": DISCLAIMER}


# ---------------------------------------------------------------------------
# Simulate-risk input model
# ---------------------------------------------------------------------------

class Tx(BaseModel):
    """A single simulated transaction for the Early Warning screen."""
    sender_account: str
    receiver_account: str
    amount: float
    timestamp: str
    sender_bank: str = "Bank Alpha"
    receiver_bank: str = "Bank Alpha"
    transaction_type: str = "Transfer"


@app.post("/simulate-risk")
def simulate(txs: list[Tx], escalation_rule: bool = False) -> dict:
    """Assess a new hypothetical scenario against all known reported cases.

    Uses the existing assess_case implementation and weights unchanged
    (connection 40 %, pattern similarity 35 %, anomaly 25 %).
    is_synthetic_suspicious is set to 'No' for simulation rows and is NOT
    passed to any model – it is a schema requirement only.

    Optional escalation_rule flag (default False): elevates risk_level to
    'High priority for review' if case matches >= 2 known reported cases above
    similarity threshold and has anomaly > 0.8.

    Returns risk_score, risk_level (priority-for-review wording), components,
    closest known cases, matched features, reasons and disclaimer.
    No block/freeze action exists.
    """
    if not txs:
        raise HTTPException(status_code=400, detail="At least one transaction is required.")

    rows = [
        {
            "transaction_id": f"SIM{i:03d}",
            "case_id": "CASE_NEW",
            "transaction_type": t.transaction_type,
            # is_synthetic_suspicious is a schema column, not a model input
            "is_synthetic_suspicious": "No",
            "source": "simulation",
            "sender_bank": t.sender_bank,
            "receiver_bank": t.receiver_bank,
            "sender_account": t.sender_account,
            "receiver_account": t.receiver_account,
            "amount": t.amount,
            "timestamp": t.timestamp,
        }
        for i, t in enumerate(txs)
    ]
    new_df = pd.DataFrame(rows)
    new_df["timestamp"] = pd.to_datetime(new_df["timestamp"])
    new_df["amount"] = new_df["amount"].astype(float)

    result = assess_case(
        new_df,
        state.engine,
        state.anomaly,
        state.reported,
        state.cal["threshold"],
        existing_df=state.df,
        escalation_rule=escalation_rule,
    )
    return {"case_id": "CASE_NEW", **result, "disclaimer": DISCLAIMER}
