# Opsight

## Live Demo

Frontend

https://agreeable-cliff-08bf3bd0f.2.azurestaticapps.net

API Docs (Swagger)

https://opsight-api.calmstone-581ea79a.eastus.azurecontainerapps.io/docs

Health Check

https://opsight-api.calmstone-581ea79a.eastus.azurecontainerapps.io/health

## What Is Opsight?

Opsight is an end-to-end operational analytics project that takes raw business-style datasets and turns them into usable analysis outputs.

It combines:

- a modular Python data pipeline
- a FastAPI backend
- a React frontend
- analytics, anomaly detection, and chart visualization

In one flow, a user can load a dataset, run processing, review quality metrics, inspect charts, and run anomaly or prediction models.

## Problem It Solves

Many teams receive data that is inconsistent across files and systems. Before any useful analysis, that data must be standardized and validated.

Opsight demonstrates a practical solution:

- ingest heterogeneous tabular data
- normalize records into one canonical structure
- validate records before storage
- expose analysis results through API endpoints and UI views

## How It Works

### Pipeline Path

- Ingestion: load source data (CSV, JSON, Parquet, XLSX, and common URL sources)
- Normalization: map source rows to canonical records
- Validation: apply record checks and quality rules
- Storage: persist valid records (JSON or Parquet)
- Analytics Surface: serve metrics, charts, anomaly detection, and prediction through FastAPI + React

### System Flow

```text
Source Data
	|
	v
Ingestion -> Adapter -> Canonical Records -> Validation -> Persistence
														|
														v
											   Reports and Logs
														|
														v
												FastAPI Endpoints
														|
							-------------------------------------------------
							|                                               |
							v                                               v
					 React Frontend                                 Legacy Streamlit UI
```

### Canonical Record Contract

All datasets are normalized to the same record shape:

```json
{
	"entity_id": "str",
	"timestamp": "str",
	"features": "dict",
	"metadata": "dict"
}
```

## Why It Matters

Opsight is useful as a real engineering example because it shows how data work is delivered as a complete product path, not only isolated scripts.

Practical value demonstrated in this repository:

- modular pipeline design from ingestion to storage
- structured data processing with explicit contracts
- observable runs via summaries and logs
- analytics and anomaly detection exposed in a user-facing interface
- test coverage across backend and frontend behavior

## What Is Implemented Today

### Frontend

- Dataset tab to select and run datasets
- Metrics tab for ingestion and validation counts
- Charts tab for generated visualizations and dataset overview
- Anomaly Detection tab (Z-Score, Isolation Forest, K-Means)
- Prediction tab (Linear Regression, Moving Average)

### Backend API

- health and version endpoint
- pipeline trigger and status endpoints
- session state and reset endpoints
- chart image and overview endpoints
- anomaly and prediction endpoints
- static chart asset serving

For endpoint details and examples, see API_DOCUMENTATION.md.

## Quick Start

### Option 1: Windows one-command startup

From repository root:

```powershell
start_opsight.bat
```

Starts:

- backend API at http://localhost:8000
- frontend UI at http://localhost:5173

Stop services:

```powershell
stop_opsight.bat
```

### Option 2: Manual startup

Create and activate virtual environment:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

Install backend dependencies:

```powershell
pip install -r requirements.txt
```

Install frontend dependencies:

```powershell
cd modules/frontend
npm install
cd ../..
```

Create local environment file:

```powershell
Copy-Item .env.example .env
```

Start backend API:

```powershell
uvicorn modules.api.app:app --reload
```

Start frontend UI (second terminal):

```powershell
cd modules/frontend
npm run dev
```

Open:

- UI: http://localhost:5173
- API: http://localhost:8000
- Health: http://localhost:8000/health

## Typical Local Review Flow

1. Open Dataset tab
2. Run a dataset through the pipeline
3. Check Metrics
4. Inspect Charts
5. Run Anomaly Detection
6. Run Prediction

## Deployment Notes

Opsight supports split frontend and backend deployment.

Frontend environment examples: modules/frontend/.env.example
Backend environment templates: .env.example, configs/production.env

Production configuration is split across three places:

- repo-tracked templates for documented keys only
- GitHub deployment secrets and variables for workflow execution
- Azure runtime settings and secrets for the live service

For the backend, production runtime must define APP_ENV=prod, disable local fallback, and provide Blob ingestion settings.

For the current deployment target, the backend runtime is Azure Container Apps opsight-api in rg-opsight-dev, and runtime secrets should live in Azure Container Apps secrets rather than in the repository.

For the frontend, production builds should supply the deployed API URL through deployment configuration rather than relying on local dev proxy behavior.

This repo includes a frontend deployment workflow for Azure Static Web Apps at .github/workflows/deploy-frontend.yml. It expects the deploy token in AZURE_STATIC_WEB_APPS_API_TOKEN and frontend build-time URLs in GitHub repository variables.

If the frontend is deployed on a different origin from the API, the backend must also set CORS_ALLOWED_ORIGINS to include the deployed frontend URL.

The source of truth for the production environment and secrets contract is configs/README.md.

For a local preflight check of the backend runtime contract, run validate_opsight_runtime.bat.

For a full live deployment verification pass, run run_live_smoke_tests.bat with the frontend and API URLs.

Deployment runbook and rollback steps are documented in reports/deployment_runbook.md.

## Repository Map

```text
opsight/
|-- configs/            runtime and deployment configuration
|-- data/               sample datasets and persisted records
|-- logs/               pipeline execution logs
|-- modules/
|   |-- adapter/        source-to-canonical mapping
|   |-- api/            FastAPI service and routes
|   |-- config/         runtime and storage configuration
|   |-- frontend/       React + Vite application
|   |-- ingestion/      source loading and format detection
|   |-- intelligence/   analysis-related modules
|   |-- ml/             anomaly detection and prediction models
|   |-- persistence/    storage backends
|   |-- streamlit_ui/   legacy internal dashboard
|   |-- validation/     record validation and quality checks
|   `-- visualization/  chart generation
|-- reports/            run summaries and failure summaries
|-- tests/              backend and integration tests
|-- run_pipeline.py     pipeline entrypoint
|-- start_opsight.bat   local startup helper
`-- stop_opsight.bat    local shutdown helper
```

## Testing

From repository root:

```powershell
python -m pytest
```

Frontend tests:

```powershell
cd modules/frontend
npm test
```

Frontend build check:

```powershell
cd modules/frontend
npm run build
```

## Tech Stack

- Backend: Python, FastAPI, Pandas, scikit-learn, Matplotlib
- Frontend: React, Vite, Vitest
- Storage: JSON and Parquet backends, with cloud integration hooks

## License

This project is licensed under the MIT License. See LICENSE.