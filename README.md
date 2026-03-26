# Opsight

Opsight is a portfolio-ready operational analytics project that turns raw business datasets into a usable analysis workflow.

It combines a modular Python data pipeline, a FastAPI backend, a React frontend, chart generation, anomaly detection, and lightweight prediction tools. A user can select a dataset, run the pipeline, inspect summary metrics, explore charts, and execute anomaly detection or prediction models from one interface.

## What Opsight Does

Opsight is built for the common real-world problem of operational data arriving in inconsistent formats and needing to become usable quickly.

At a high level, Opsight:

- ingests tabular source data such as CSV, JSON, Parquet, and Excel
- maps source rows into a canonical record format
- validates records before persistence
- stores processed records for downstream analysis
- exposes backend endpoints for charts, session state, anomaly detection, and prediction
- provides a React UI with Dataset, Metrics, Charts, Anomaly Detection, and Prediction tabs

## Why It Matters

Opsight is designed to show more than isolated scripts or notebooks.

It demonstrates how to:

- structure a data product as a modular pipeline
- separate backend processing from frontend presentation
- carry data from ingestion through validation to analysis
- expose analytical capabilities through a usable UI
- validate behavior with automated tests across backend and frontend layers

## Current Product Surface

### Frontend UI

The React frontend currently provides these tabs:

- Dataset: choose a sample dataset, target local or deployed API, and trigger the pipeline
- Metrics: review pipeline counts such as ingested, valid, invalid, and persisted records
- Charts: load generated visualizations and dataset overview statistics
- Anomaly Detection: run anomaly models such as Z-Score, Isolation Forest, and K-Means
- Prediction: run forecasting-oriented models such as Linear Regression and Moving Average

### Backend API

The FastAPI service currently provides:

- health and version reporting
- pipeline trigger and session reset/state endpoints
- chart generation and chart overview endpoints
- anomaly detection endpoints
- prediction endpoints
- static asset serving for generated chart images

### Data Pipeline

The Python pipeline currently handles:

- dataset ingestion
- schema normalization through adapter logic
- canonical record creation
- validation and duplicate checks
- persistence to local storage
- run summaries, failure summaries, and structured logs

## High-Level Architecture

```text
Dataset Source
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

## Canonical Record Shape

Opsight normalizes records into a consistent structure so the rest of the system can work against one contract.

```python
{
    "entity_id": str,
    "timestamp": str,
    "features": dict,
    "metadata": dict,
}
```

## Key Capabilities

### Dataset Handling

Opsight supports multiple source formats in the ingestion layer, including:

- CSV and TSV
- JSON
- Parquet
- Excel
- HTTP and HTTPS file URLs for common tabular formats

### Charts

The charts workflow currently includes:

- histogram
- category bar chart
- box plot
- scatter plot
- grouped comparison chart
- dataset overview statistics

### Anomaly Detection

The anomaly detection workflow currently includes:

- Z-Score baseline
- Isolation Forest
- K-Means clustering

### Prediction

The prediction workflow currently includes:

- Linear Regression
- Moving Average

## Quick Start

### Option 1: Windows One-Command Startup

From the repository root:

```bat
start_opsight.bat
```

This starts:

- backend API on `http://localhost:8000`
- frontend UI on `http://localhost:5173`

To stop local processes:

```bat
stop_opsight.bat
```

### Option 2: Manual Local Setup

#### 1. Create and activate a virtual environment

PowerShell:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

#### 2. Install Python dependencies

```bash
pip install -r requirements.txt
```

#### 3. Install frontend dependencies

```bash
cd modules/frontend
npm install
cd ../..
```

#### 4. Create local environment file

```powershell
Copy-Item .env.example .env
```

Minimum local defaults already exist in `.env.example`. The most important value to review is:

- `UPLOAD_ACCESS_CODE`

#### 5. Start the backend API

From repository root:

```bash
uvicorn modules.api.app:app --reload
```

#### 6. Start the frontend UI

In a second terminal:

```bash
cd modules/frontend
npm run dev
```

#### 7. Open the app

- Frontend UI: `http://localhost:5173`
- Backend API: `http://localhost:8000`
- Health endpoint: `http://localhost:8000/health`

## Using the App Locally

A typical local flow is:

1. Open the Dataset tab.
2. Select a sample dataset.
3. Run the pipeline against the local API.
4. Review Metrics.
5. Open Charts for visual analysis.
6. Run Anomaly Detection models.
7. Run Prediction models after the pipeline completes.

## Deployed Usage

Opsight is structured to support a deployed frontend and API split.

### Frontend API Targeting

The frontend supports local and deployed API targets. Relevant frontend environment options are in [modules/frontend/.env.example](modules/frontend/.env.example).

Important settings:

- `VITE_API_BASE_URL`
- `VITE_API_PROXY_TARGET`
- `VITE_API_PROXY_TARGET_LOCAL`

### Backend Runtime Configuration

Runtime settings are defined through environment variables. The local baseline is in [.env.example](.env.example), and production-oriented defaults are in [configs/production.env](configs/production.env).

Important backend settings:

- `APP_ENV`
- `APP_VERSION`
- `PORT`
- `UPLOAD_ACCESS_CODE`
- `PERSISTENCE_MODE`
- `STORAGE_PATH`
- `LOG_LEVEL`
- `ALLOW_LOCAL_FALLBACK`

Optional cloud-related settings include:

- `BLOB_ACCOUNT`
- `BLOB_CONTAINER`
- `BLOB_PATH`
- `API_BASE_URL`
- `AZURE_STORAGE_CONNECTION_STRING`
- `AZURE_STORAGE_CONTAINER`
- `AZURE_KEY_VAULT_URL`
- `AZURE_OPENAI_API_KEY`
- `AZURE_OPENAI_ENDPOINT`

### Docker

Build the image:

```bash
docker build -t opsight:final .
```

Run the API container:

```bash
docker run --rm -p 8000:8000 --name opsight-api opsight:final
```

Or use Docker Compose:

```bash
docker compose up --build
```

## Repository Map

```text
opsight/
├── configs/            runtime and deployment configuration
├── data/               sample datasets and persisted records
├── logs/               pipeline execution logs
├── modules/
│   ├── adapter/        source-to-canonical mapping
│   ├── api/            FastAPI service and routes
│   ├── config/         runtime and storage configuration
│   ├── frontend/       React + Vite application
│   ├── ingestion/      source loading and format detection
│   ├── intelligence/   analysis-related modules
│   ├── ml/             anomaly detection and prediction models
│   ├── persistence/    storage backends
│   ├── streamlit_ui/   legacy internal dashboard
│   ├── validation/     record validation and quality checks
│   └── visualization/  chart generation
├── reports/            run summaries and failure summaries
├── tests/              backend and integration tests
├── run_pipeline.py     pipeline entrypoint
├── start_opsight.bat   local startup helper
└── stop_opsight.bat    local shutdown helper
```

## Testing

### Backend and pipeline tests

From repository root:

```bash
python -m pytest
```

### Frontend tests

```bash
cd modules/frontend
npm test
```

### Frontend build

```bash
cd modules/frontend
npm run build
```

## Tech Stack

### Backend

- Python
- FastAPI
- Pandas
- Pydantic
- scikit-learn
- Matplotlib

### Frontend

- React
- Vite
- Vitest

### Data and Storage

- JSON
- Parquet
- Azure Blob integration hooks

## Status

Opsight is actively developed, but it already works as an end-to-end demonstration of dataset ingestion, validation, persistence, charting, anomaly detection, and prediction through a combined backend and UI workflow.

## License

This project is licensed under the MIT License. See [LICENSE](LICENSE).
