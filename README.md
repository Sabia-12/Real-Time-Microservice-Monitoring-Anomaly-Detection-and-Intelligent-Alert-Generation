# Real-Time Microservice Monitoring, Anomaly Detection and Intelligent Alert Generation

Real-time microservice monitoring, statistical & ML anomaly detection, intelligent alert aggregation, and incident correlation for the **Google Online Boutique** microservice application.

---

## Architecture Overview

```
                                  ┌──────────────────────────────┐
                                  │   RE2-OB Case Parquet Data   │
                                  │ (metrics, logs, traces, inj) │
                                  └──────────────┬───────────────┘
                                                 │
                                       [ Replay Engine ]
                                                 │ (stream rows @ 1s)
                                                 ▼
┌───────────────────────┐            ┌───────────────────────────┐
│ Live Prometheus Scrap │ (Phase 5)  │  Preprocessing & Detector │
│ (cAdvisor, node-exp)  ├───────────►│ (ZScore-max-7.0 baseline) │
└───────────────────────┘            └─────────────┬─────────────┘
                                                   │ Anomaly Event
                                                   ▼
                                     ┌───────────────────────────┐
                                     │       Alert Engine        │
                                     │ 1. Cooldown Deduplication │
                                     │ 2. Severity Scoring       │
                                     │ 3. Log/Trace Enrichment   │
                                     │ 4. Service Graph Grouping │
                                     └─────────────┬─────────────┘
                                                   │
                       ┌───────────────────────────┴───────────────────────────┐
                       ▼                                                       ▼
            ┌───────────────────────┐                               ┌───────────────────────┐
            │   SQLAlchemy Models   │                               │     FastAPI App       │
            │  (SQLite Development) │                               │  REST + SSE Stream    │
            │ Services, Anomalies,  │                               │ /api/services, alerts │
            │   Alerts, Incidents   │                               │ /api/events (SSE)     │
            └───────────────────────┘                               └───────────┬───────────┘
                                                                                │
                                                                                ▼
                                                                    ┌───────────────────────┐
                                                                    │    React Dashboard    │
                                                                    │  (VITE_API_BASE_URL)  │
                                                                    └───────────────────────┘
```

---

## Project Structure

```
├── backend/
│   ├── alerts/          # Deduplication, topological incident grouping, severity & enrichment
│   ├── app/
│   │   ├── api/         # FastAPI REST endpoints & Server-Sent Events stream
│   │   ├── db/          # SQLAlchemy models, SQLite session & initial service seeds
│   │   ├── events.py    # SSE broadcaster hub
│   │   ├── main.py      # Application entrypoint & CORS middleware
│   │   └── replay.py    # Historical RE2-OB streaming engine
│   ├── detection/       # Rolling Z-score baseline, Isolation Forest, OCSVM, LOF detectors
│   ├── preprocessing/   # Data loader, cleaner, sliding-window feature extractor, splitters
│   ├── requirements.txt # Python dependencies
│   └── tests/           # 46 automated unit and integration tests (pytest + httpx)
├── src/                 # React + Vite dashboard (Pages, Components, Recharts, Lucide)
├── data/raw/            # RE2-OB benchmark parquet datasets (excluded from git)
├── data-analysis/       # Evaluation reports and benchmark JSON outputs
├── docs/                # Architecture documentation, API contracts, evaluation reports
└── package.json         # Frontend configuration
```

---

## Quickstart

### 1. Backend Setup & Tests
```bash
# Set up virtual environment
python -m venv .venv
source .venv/bin/activate  # Or on Windows: .\.venv\Scripts\Activate.ps1

# Install dependencies
pip install -r backend/requirements.txt

# Run the test suite (46 passing tests)
pytest backend/tests -v

# Start the FastAPI server
uvicorn backend.app.main:app --host 127.0.0.1 --port 8000 --reload
```
- API Docs: `http://localhost:8000/docs`
- Health check: `http://localhost:8000/api/health`

### 2. Frontend Setup
```bash
# Install frontend dependencies
npm install

# Start Vite development server
npm run dev
```
- Web Dashboard: `http://localhost:5173`
- Configured to talk to the backend via `VITE_API_BASE_URL=http://localhost:8000` in `.env`.

### 3. Historical Replay
Stream any of the 90 real RE2-OB cases at configurable speeds through the preprocessing, detection, and alerting pipeline:
```bash
curl -X POST "http://localhost:8000/api/replay/start?case_id=re2ob_checkoutservice_cpu_1&speed=10"
```
Live updates stream directly to the dashboard via Server-Sent Events (SSE).
