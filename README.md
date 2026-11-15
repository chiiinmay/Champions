# SHADOWNET — Cross-Case Financial Fraud Intelligence

> **Prototype for investigative leads only. All data is synthetic. No real payments are blocked or individuals implicated.**

SHADOWNET is a hackathon prototype that simulates shared intelligence across multiple banks, surfacing structural similarities between reported cases to assist human investigators. It does **not** determine guilt, block payments, or handle real data.

---

## Project Structure

```
Champions/
├── backend/              # FastAPI application
│   ├── main.py           # API routes
│   ├── state.py          # In-memory state loader
│   ├── anomaly_detection.py
│   ├── cross_case_detection.py
│   ├── feature_extraction.py
│   ├── fingerprint_engine.py
│   ├── graph_engine.py
│   ├── money_flow.py
│   ├── risk_assessment.py
│   └── similarity_engine.py
├── dataset/              # Synthetic transaction data (do not modify)
│   └── transactions.csv
├── evaluation/           # Analysis scripts and results
│   ├── export_pattern_output.py
│   ├── export_graph_output.py
│   ├── stress_tests.py
│   └── results/
├── frontend/             # Vite + React dashboard (6 pages)
│   ├── src/
│   │   ├── api.js        # All API calls — base URL set here
│   │   ├── App.jsx       # Router + sidebar + layout
│   │   ├── components/
│   │   │   ├── DisclaimerBanner.jsx
│   │   │   ├── RiskBadge.jsx
│   │   │   └── StatusNotice.jsx
│   │   └── pages/
│   │       ├── Overview.jsx
│   │       ├── NetworkExplorer.jsx
│   │       ├── PatternFingerprinting.jsx
│   │       ├── MoneyTrail.jsx
│   │       ├── EarlyWarning.jsx
│   │       └── Upload.jsx
│   └── vite.config.js
├── tests/
│   ├── test_patterns.py    # Phase 3 + hub-consistency test
│   └── test_integration.py # Phase 4a endpoint tests
└── documentation/
```

---

## Running the Demo

You need **two terminals** open in PowerShell.

### Prerequisites

```powershell
# From the project root — install Python dependencies
.\.venv\Scripts\pip.exe install -r requirements.txt

# Install frontend dependencies (first time only)
cd frontend
npm install
cd ..
```

### Terminal 1 — Backend (FastAPI)

```powershell
cd C:\Users\User\OneDrive\Desktop\Champions
.\.venv\Scripts\uvicorn.exe backend.main:app --port 8000
```

The API will be available at **http://localhost:8000**. Interactive docs at http://localhost:8000/docs.

### Terminal 2 — Frontend (Vite dev server)

```powershell
cd C:\Users\User\OneDrive\Desktop\Champions\frontend
npm run dev
```

Then open **http://localhost:5173** in your browser.

> **Note:** The frontend dev server is pinned to port 5173 (`strictPort: true`) because backend CORS only allows `http://localhost:5173`.

---

## Pages & Endpoints

| Page | Route | Backend Endpoints |
|---|---|---|
| Overview | `/overview` `/cases` | `GET /overview`, `GET /cases` |
| Network Explorer | `/graph` `/discover-connections` | `GET /graph`, `POST /discover-connections` |
| Pattern Fingerprinting | `/compare-patterns` | `POST /compare-patterns` |
| Money Trail | `/money-trail/:case_id` | `GET /money-trail/{case_id}` |
| Early Warning | `/simulate-risk` | `POST /simulate-risk` |
| Upload | `/upload-transactions` | `POST /upload-transactions` |

---

## Running Tests

```powershell
cd C:\Users\User\OneDrive\Desktop\Champions
.\.venv\Scripts\python.exe -m pytest -v
```

**35 tests** (8 pattern tests + 1 hub-consistency + 18 integration + stress/export tests) must all pass.

---

## Production Build (Frontend)

```powershell
cd C:\Users\User\OneDrive\Desktop\Champions\frontend
npm run build
```

Output goes to `frontend/dist/`. The bundle is offline-ready — no CDN scripts, no web fonts, no external images.

---

## API Quick Reference

```
GET  /health                    # Liveness check
GET  /overview                  # Aggregate stats
GET  /cases                     # All cases ranked by risk_score (desc)
GET  /transactions              # Raw transaction list
GET  /graph?cases=CASE_A,...    # Cytoscape-ready graph data
POST /upload-transactions       # Upload new transactions (in-memory only)
POST /discover-connections      # Cross-case shared accounts and connections
POST /compare-patterns          # Pairwise similarity matrix
GET  /money-trail/{case_id}     # Chronological trail with paths and splits
POST /simulate-risk             # Risk assessment for ad-hoc transaction sets
```

`/simulate-risk` accepts an optional query param `?escalation_rule=true` to enable the documented escalation rule (default **off**).

---

## Key Design Decisions

- **No payment blocking.** The system surfaces investigative leads; all actions are taken by human investigators.
- **No `is_synthetic_suspicious` as model input.** The ground-truth label column is excluded from all feature extraction and risk scoring.
- **Hub filtering.** Accounts appearing in many cases (default threshold: 20 connections) are excluded from connection discovery to avoid false positives. The threshold and reasoning are documented in `documentation/hub_filtering_principle.md`.
- **Escalation rule (off by default).** A case is flagged High priority if its similarity to ≥ 2 known cases exceeds the calibrated threshold **(strict `>`)** and its anomaly score exceeds 0.8. Enable with `?escalation_rule=true`.
- **Synthetic data only.** All transactions are generated for this prototype. A real deployment would require data-sharing agreements and privacy controls.

---

## Disclaimer

> This prototype simulates a shared intelligence view across banks. A real deployment would need data-sharing agreements and privacy controls. All findings are investigative leads for human review, not proof of criminal activity. SHADOWNET does not block payments or determine guilt.
