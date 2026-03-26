# Opsight

Opsight is an end-to-end operational analytics app that turns raw business datasets into usable analysis outputs.

It combines:
- a modular Python pipeline for ingestion, normalization, validation, and persistence
- a FastAPI backend for data, chart, and ML endpoints
- a React UI for dataset runs, metrics, charts, anomaly detection, and prediction

If you are new to the repo, this README is designed so you can understand the project in under two minutes and run it quickly.

## Why Opsight Matters

In real operations work, data rarely arrives clean or consistent. Opsight demonstrates a practical flow:
1. ingest heterogeneous data
2. normalize to a canonical record contract
3. validate quality before persistence
4. expose analysis through a user-facing UI

The goal is not just model output. The goal is a usable product path from raw data to explainable insights.

## What Opsight Does Today

### UI (current tabs)
- Dataset: choose a dataset and trigger a pipeline run
- Metrics: view ingested, valid, invalid, and persisted counts
- Charts: generate visualizations and review dataset-level stats
- Anomaly Detection: run Z-Score, Isolation Forest, or K-Means
- Prediction: run Linear Regression or Moving Average forecasts

### Backend
- health and version reporting
- dataset pipeline trigger and session state endpoints
- chart image generation endpoints
- anomaly and prediction endpoints
- static chart asset serving

### Pipeline
- ingestion from supported formats (CSV, JSON, Parquet, XLSX)
- schema normalization to canonical records
- validation and quality checks
- local persistence for downstream analysis
- run summaries and logs for observability

## High-Level Architecture

```text
Source Data
    |
    v
Ingestion -> Adapter -> Canonical Records -> Validation -> Persistence
                                                        |
                                                        v
                                                FastAPI Endpoints
                                                        |
                              --------------------------------------------
                              |                                          |
                              v                                          v
                         React UI                               Reports and Logs
```

## Canonical Record Contract

All records are normalized into this shape:

```python
{
  "entity_id": str,
  "timestamp": str,
  "features": dict,
  "metadata": dict,
}
```

This keeps downstream logic consistent across different source datasets.

## Quick Start (Local)

### Option 1: One-command startup (Windows)

From repo root:

```bat
start_opsight.bat
```

This starts:
- backend API: http://localhost:8000
- frontend UI: http://localhost:5173

Stop services:

```bat
stop_opsight.bat
```

### Option 2: Manual startup

1. Create and activate virtual environment:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

2. Install backend dependencies:

```bash
pip install -r requirements.txt
```

3. Install frontend dependencies:

```bash
cd modules/frontend
npm install
cd ../..
```

4. Set local environment file:

```powershell
Copy-Item .env.example .env
```

5. Start backend:

```bash
uvicorn modules.api.app:app --reload
```

6. Start frontend (second terminal):

```bash
cd modules/frontend
npm run dev
```

7. Open:
- UI: http://localhost:5173
- API health: http://localhost:8000/health

## Typical User Flow

1. Open Dataset tab
2. Select a dataset and run pipeline
3. Review Metrics
4. Open Charts
5. Run Anomaly Detection models
6. Run Prediction models

## Deployed Usage Guidance

Opsight is structured for split frontend/backend deployment.

### Frontend runtime targeting
Frontend URL behavior is controlled by environment variables in `modules/frontend`.

Important variables:
- `VITE_API_BASE_URL`
- `VITE_LOCAL_API_URL`
- `VITE_CLOUD_API_URL`
- `VITE_API_PROXY_TARGET`
- `VITE_API_PROXY_TARGET_LOCAL`

Behavior:
- `npm run dev`: uses Vite proxy routes (`/api-local`, `/api-cloud`)
- `npm run build`: uses real URLs (`VITE_LOCAL_API_URL`, `VITE_CLOUD_API_URL`, or defaults)

### Backend runtime configuration
Primary runtime config comes from environment variables.

Base templates:
- `.env.example`
- `configs/production.env`

Common settings:
- `APP_ENV`
- `APP_VERSION`
- `PORT`
- `UPLOAD_ACCESS_CODE`
- `PERSISTENCE_MODE`
- `STORAGE_PATH`
- `LOG_LEVEL`
- `PIPELINE_SUMMARY_PATH`

## API Surface (summary)

Key endpoint groups:
- health: `/health`
- session: `/session/state`, `/session/reset`
- pipeline: `/pipeline/trigger`, `/pipeline/status`
- charts: `/charts/*`, `/charts/overview`
- ML anomaly: `/ml/anomaly/*`
- ML prediction: `/ml/prediction/*`

## Testing

### Backend tests

From repo root:

```bash
python -m pytest
```

### Frontend tests

```bash
cd modules/frontend
npm test
```

### Frontend build check

```bash
cd modules/frontend
npm run build
```

## Repository Map

```text
opsight/
|- configs/            runtime and deployment configuration
|- data/               sample datasets and persisted records
|- logs/               runtime and pipeline logs
|- modules/
|  |- adapter/         source-to-canonical mapping
|  |- api/             FastAPI app and routes
|  |- config/          runtime/storage config
|  |- frontend/        React + Vite UI
|  |- ingestion/       source readers and normalization helpers
|  |- intelligence/    analytics helpers
|  |- ml/              anomaly and prediction models
|  |- persistence/     storage backends
|  |- streamlit_ui/    legacy internal UI
|  |- validation/      quality and contract checks
|  '- visualization/   chart generation
|- reports/            run summaries and failure summaries
|- tests/              backend and integration tests
|- run_pipeline.py     pipeline entrypoint
|- start_opsight.bat   local startup helper
'- stop_opsight.bat    local shutdown helper
```

## Tech Stack

- Backend: Python, FastAPI, Pandas, scikit-learn
- Frontend: React, Vite, Vitest
- Storage: JSON/Parquet local persistence with cloud-oriented hooks

## Project Status

Opsight is actively developed and already supports a complete demo path from dataset ingestion to charts, anomaly detection, and prediction in a single UI.

## License

MIT License. See `LICENSE`.
