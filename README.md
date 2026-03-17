# Opsight

Opsight is a modular operational data pipeline for ingesting heterogeneous datasets, normalizing them into a canonical schema, validating data integrity, and persisting validated records for downstream analytics.

The project is structured around small, composable pipeline stages and a single orchestration entrypoint. The repository already includes a working end-to-end runner, sample datasets, JSON and Parquet persistence backends, reporting artifacts, and unit tests covering both success and failure paths.

## Pipeline Overview

```text
Opsight Pipeline Architecture
               ┌───────────────┐
               │   Source Data │
               │ CSV / JSON /  │
               │ Parquet / API │
               └───────┬───────┘
                       │
                       ▼
               ┌───────────────┐
               │   Ingestion   │
               │ Load dataset  │
               │ Basic checks  │
               └───────┬───────┘
                       │
                       ▼
               ┌───────────────┐
               │    Adapter    │
               │ Normalize     │
               │ Map schema    │
               └───────┬───────┘
                       │
                       ▼
               ┌───────────────┐
               │  Canonical    │
               │    Records    │
               │ entity_id     │
               │ timestamp     │
               │ features{}    │
               └───────┬───────┘
                       │
                       ▼
               ┌───────────────┐
               │  Validation   │
               │ Field checks  │
               │ duplicates    │
               │ timestamps    │
               └───────┬───────┘
                       │
                       ▼
               ┌───────────────┐
               │  Persistence  │
               │ JSON / Parquet│
               │ storage layer │
               └───────┬───────┘
                       │
                       ▼
               ┌───────────────┐
               │ Observability │
               │ Logs          │
               │ Run summary   │
               │ Error reports │
               └───────────────┘
```

The system emphasizes:

- modular pipeline stages
- clear data contracts
- centralized orchestration
- observability through logs and run summaries
- testable failure handling

## What The Project Does Today

Opsight currently ships with a runnable pipeline in `run_pipeline.py` that:

1. ingests a source dataset from the `data/` directory
2. adapts the source rows into a canonical record shape
3. validates each canonical record
4. persists valid records through the configured storage backend
5. writes a run summary and stage logs for observability

The default pipeline configuration reads `data/opsight_sample_sales.csv` and persists valid records to `data/records.json` using the JSON storage backend.

## Canonical Record Schema

Canonical records in Opsight follow this structure:

```python
{
    "entity_id": str,
    "timestamp": str,
    "features": dict,
    "metadata": dict,
}
```

This schema creates a consistent contract between ingestion, transformation, validation, and persistence.

## Core Modules

### Ingestion

The ingestion layer detects source format and loads data into a dataframe for downstream processing.

Currently supported source handling:

- CSV
- TSV
- JSON
- Parquet
- Excel
- HTTP and HTTPS file URLs for common tabular formats

### Adapter

The adapter layer normalizes source column names and maps source rows into the canonical Opsight record format.

Current mapping behavior:

- columns containing `id` are treated as entity identifiers
- columns containing `time` or `date` are treated as timestamps
- all remaining columns are grouped into `features`

### Validation

The validation package includes:

- canonical record validation
- timestamp validation helpers
- feature validation helpers
- duplicate detection utilities
- report and quality-report modules

The current pipeline runner validates each canonical record before persistence and separates valid and invalid records for reporting.

### Persistence

The persistence layer provides a backend abstraction with implemented support for:

- local JSON storage
- Parquet storage

Backend selection is handled through `StorageConfig` and `StorageFactory`.

## Running The Pipeline

Run the pipeline from the repository root:

```bash
python run_pipeline.py
```

Observed current sample run:

```python
{
    "status": "SUCCESS",
    "failed_stage": None,
    "records_ingested": 3,
    "records_valid": 3,
    "records_invalid": 0,
    "records_persisted": 3,
    "runtime_seconds": 0.007852,
}
```

## Generated Artifacts

When the pipeline runs, Opsight produces:

- stage logs in `logs/`
- `reports/pipeline_run_summary.json` for every run
- `reports/pipeline_failure_summary.json` when a run fails
- persisted output in `data/records.json` by default

## Testing

Install dependencies, then run the full test suite:

```bash
pip install -r requirements.txt
python -m pytest
```

If dependencies are already installed, run:

```bash
python -m pytest
```

## Deployment And Operations

### Environment Variables

Opsight reads runtime configuration from environment variables.

- `.env.example` provides a local baseline
- `configs/production.env` provides production-oriented defaults

At minimum, set these for runtime:

- `APP_ENV`
- `APP_VERSION`
- `PORT`
- `UPLOAD_ACCESS_CODE`
- `PERSISTENCE_MODE`
- `STORAGE_PATH`
- `LOG_LEVEL`
- `ALLOW_LOCAL_FALLBACK`

### Versioning Strategy (PS-096)

Opsight uses semantic versioning with release baseline `v1.0.0`.

- Version source of truth: `APP_VERSION` environment variable
- Startup observability: API startup logs include `app_version`
- Runtime observability: `GET /health` returns `version`
- Deployment updates: update `APP_VERSION` in deployment environment configuration before rollout

Recommended semantic version increments:

- `MAJOR` for breaking API or data-contract changes
- `MINOR` for backward-compatible features
- `PATCH` for backward-compatible fixes

Example deployment update:

```bash
APP_VERSION=1.0.1
```

Then deploy and confirm the release via `GET /health`.

Optional Azure settings:

- `BLOB_ACCOUNT` (required when `APP_ENV=prod`)
- `BLOB_CONTAINER` (required when `APP_ENV=prod`)
- `BLOB_PATH`
- `API_BASE_URL`
- `ENABLE_PIPELINE`
- `INPUT_SOURCE_PATH`
- `PIPELINE_SUMMARY_PATH`
- `AZURE_STORAGE_CONNECTION_STRING`
- `AZURE_STORAGE_CONTAINER`
- `AZURE_KEY_VAULT_URL`
- `AZURE_OPENAI_API_KEY`
- `AZURE_OPENAI_ENDPOINT`

### Run API Locally

From repository root:

```bash
uvicorn modules.api.app:app --host 0.0.0.0 --port 8000
```

Health check:

```bash
curl http://localhost:8000/health
```

Expected response:

```json
{"status":"ok"}
```

### Build And Run Docker Image

Build image:

```bash
docker build -t opsight:final .
```

Run API container:

```bash
docker run --rm -p 8000:8000 --name opsight-api opsight:final
```

## Branching and Release Workflow

### Branch Roles

- main: production-ready branch
- dev: active development and integration branch
- feature/*: isolated work for individual issues or changes

### Standard Flow

```text
feature/* -> dev -> main
```

### Merge Rules

- No direct commits to main
- All production-bound changes must be reviewed before merging
- Changes should merge into dev first, then be promoted to main
- main must always remain deployable
- main should only receive validated changes from dev, not ad hoc feature branches

### Release Rules

A release is considered ready when:

- Relevant issue scope is complete
- Tests pass
- Documentation is updated when behavior or configuration changes
- APP_VERSION is deliberately bumped
- The validated release is merged into main

### Conceptual Branch Protection

- Protect main
- Require pull requests for merge
- Require passing checks before merge
- Disallow force-pushes to main

## Logging and Monitoring

Opsight runtime logs are emitted as structured JSON for API, pipeline, and ingestion components.

- Logs are written to stdout by default
- Azure can ingest stdout logs through Container Apps and Log Analytics
- Key lifecycle events and categorized failures are intentionally logged
- Secret values (for example, access codes and credentials) are never logged

Structured log payloads include stable fields for queryability:

- event
- level
- timestamp
- app_env
- app_version

Additional fields are included when relevant, such as route, status, source, error_type, and error_message.

### Use Docker Compose

Start services (API + pipeline service definition):

```bash
docker compose up --build
```

Run in detached mode:

```bash
docker compose up --build -d
```

Stop services:

```bash
docker compose down
```

The current test suite covers:

- successful pipeline execution
- ingestion, adapter, validation, and persistence failure paths
- canonical record validation behavior
- duplicate detection behavior

## Repository Layout

```text
opsight/
├── configs/            storage and pipeline configuration
├── data/               sample input data and persisted records
├── logs/               pipeline execution logs
├── models/             future model artifacts
├── modules/
│   ├── adapter/        source-to-canonical mapping
│   ├── ingestion/      source loading and format detection
│   ├── persistence/    storage backends and factory
│   └── validation/     validation and quality checks
├── notebooks/          exploratory notebooks
├── reports/            pipeline summaries and failure reports
├── tests/              unit tests for pipeline and validation
├── run_pipeline.py     end-to-end pipeline entrypoint
└── README.md
```

## Sample Data

The repository includes representative source files for development and testing:

- `data/opsight_sample_customers.json`
- `data/opsight_sample_events.parquet`
- `data/opsight_sample_finance.xlsx`
- `data/opsight_sample_sales.csv`

## Project Status

Opsight is under active development, but the repository already contains a functional end-to-end pipeline path for local file-based sources. The current implementation is strongest in modular design, orchestration structure, failure reporting, and local persistence. Future work can extend configuration, richer validation orchestration, and additional source and storage integrations.

## License

This project is licensed under the MIT License. See `LICENSE` for details.
