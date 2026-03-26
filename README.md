# Opsight

Opsight is a full-stack operational analytics system that ingests business-style datasets, normalizes and validates records, persists results, and exposes analytics, charting, anomaly detection, and predictions through a FastAPI backend and React frontend.

## Live Deployment

- Frontend: https://agreeable-cliff-08bf3bd0f.2.azurestaticapps.net
- API docs (Swagger): https://opsight-api.calmstone-581ea79a.eastus.azurecontainerapps.io/docs
- API health: https://opsight-api.calmstone-581ea79a.eastus.azurecontainerapps.io/health

## What Opsight Solves

Opsight addresses a common data operations problem: incoming tabular data is often inconsistent across sources and formats.

This project demonstrates an end-to-end path to:

- ingest heterogeneous data
- normalize records to a canonical schema
- validate quality and contract rules
- persist valid records in configurable storage formats
- expose results to API and UI consumers

## Core Capabilities

- Multi-source ingestion for CSV, JSON, Parquet, XLSX, and URL-based sources
- Canonical adapter layer for field normalization
- Validation layer with valid/invalid record accounting
- Persistence layer with pluggable storage strategy
- Intelligence stage for anomaly detection and scoring
- FastAPI endpoints for ingestion, entities, status, charts, and ML
- React frontend for dataset runs, charts, and model outputs

## Architecture At A Glance

Pipeline flow:

1. Ingestion
2. Adapter
3. Validation
4. Persistence
5. Intelligence (best-effort, non-blocking)

Main backend entrypoint:

- `modules/api/app.py`

Pipeline runner:

- `run_pipeline.py`

## Repository Structure

Top-level directories of interest:

- `modules/` - application modules (api, ingestion, intelligence, ml, persistence, validation, visualization, frontend)
- `configs/` - runtime and deployment config assets
- `data/` - sample and staging datasets
- `scripts/` - runtime validation and deployment smoke-test scripts
- `tests/` - Python test suite
- `reports/` - pipeline summary and audit outputs
- `_design/` - architecture and phase documentation

## Local Development Setup (Windows PowerShell)

### 1. Create and activate virtual environment

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

### 2. Install Python dependencies

```powershell
pip install -r requirements.txt
```

### 3. Install frontend dependencies

```powershell
cd modules/frontend
npm install
cd ../..
```

## Run Modes

### Dev mode (local API + local Vite)

```powershell
./start_opsight.bat
```

Starts:

- Backend: http://localhost:8000
- Frontend: http://localhost:5173

### Live proxy preview (local Vite + deployed API)

```powershell
./start_opsight_live_preview.bat
```

Starts:

- Frontend preview: http://127.0.0.1:4174
- Proxies requests to deployed API

### Production preview (local production-like run)

```powershell
./start_opsight_production.bat
```

Uses `configs/production.env`, builds frontend, then starts:

- Backend: http://127.0.0.1:8000 (or configured `PORT`)
- Frontend preview: http://127.0.0.1:4173

### Stop local services

```powershell
./stop_opsight.bat
```

## Pipeline Execution

Run the full pipeline directly:

```powershell
python run_pipeline.py
```

Pipeline run summaries are written to:

- `reports/pipeline_run_summary.json`
- `reports/pipeline_failure_summary.json` (on failure)

## Testing

### Python tests

```powershell
pytest -q
```

### Frontend tests

```powershell
cd modules/frontend
npm test
```

### Live deployment smoke test

```powershell
./run_live_smoke_tests.bat <frontend-url> <api-url> [dataset-id]
```

### Azure runtime validation

```powershell
./validate_opsight_runtime.bat [path-to-env-file]
```

## API

When running locally, open:

- Swagger UI: http://localhost:8000/docs
- OpenAPI JSON: http://localhost:8000/openapi.json
- Health endpoint: http://localhost:8000/health

## Deployment Notes

- Frontend is deployed to Azure Static Web Apps.
- Backend is deployed to Azure Container Apps.
- Supporting deployment and audit docs are available in `reports/` and `_design/`.

## Tech Stack

- Backend: Python, FastAPI, Uvicorn, Pandas, Pydantic
- ML/Analytics: scikit-learn, Matplotlib
- Data formats: CSV, JSON, Parquet, XLSX
- Frontend: React + Vite
- Cloud: Azure Static Web Apps + Azure Container Apps + Azure Blob Storage

## License

This project is licensed under the MIT License. See `LICENSE`.