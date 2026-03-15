# Opsight

Opsight is an experimental operational data pipeline for ingesting, normalizing, validating, and preparing structured data for analytics and machine learning workflows.

The system uses a modular pipeline architecture, allowing new data sources, validation rules, and storage backends to be added without modifying the core flow.

## Pipeline Overview

Opsight processes data through these stages:

```text
source data
  -> ingestion
  -> adapter
  -> validation
  -> persistence
```

## Module Responsibilities

### Ingestion

Reads raw datasets from heterogeneous source systems and prepares them for pipeline processing.

Responsibilities:
- detect source file formats
- load datasets from disk
- perform basic source record validation

### Adapter

Transforms source records into the Opsight canonical schema.

Responsibilities:
- normalize source records
- map heterogeneous schemas to canonical format
- enforce canonical record structure

### Validation

Validates canonical records and produces quality reporting artifacts.

Responsibilities:
- canonical schema validation
- timestamp validation
- feature validation
- duplicate detection
- validation summary reporting
- quality report generation

### Persistence

Stores validated records using configurable storage backends.

Responsibilities:
- abstract storage interface
- local file storage
- parquet storage backend
- storage configuration and metadata tracking

Status: Storage module and persistence backends implemented. Full pipeline integration occurs in Phase 4.

## Canonical Record Structure

Records in the pipeline follow this canonical schema:

```python
{
    "entity_id": str,
    "timestamp": str,
    "features": dict,
    "metadata": dict,
}
```

This schema provides a consistent structure for validation and downstream analytics workflows.

## Repository Layout

```text
opsight/
├── modules/
│   ├── ingestion/
│   │   ├── ingestion.py
│   │   ├── data_contract.md
│   │   └── module_brief.md
│   ├── adapter/
│   │   ├── adapter.py
│   │   ├── data_contract.md
│   │   └── module_brief.md
│   ├── validation/
│   │   ├── validator.py
│   │   ├── batch_validator.py
│   │   ├── timestamp_validation.py
│   │   ├── feature_validation.py
│   │   ├── duplicate_check.py
│   │   ├── report.py
│   │   ├── quality_report.py
│   │   ├── data_contract.md
│   │   └── module_brief.md
│   └── persistence/
│       ├── storage_interface.py
│       ├── local_storage.py
│       ├── parquet_storage.py
│       ├── storage_factory.py
│       ├── persistence_manager.py
│       ├── storage_metadata.py
│       ├── storage_error.py
│       ├── data_contract.md
│       └── module_brief.md
├── data/               sample source datasets
├── notebooks/          experimentation notebooks
├── reports/            generated pipeline reports
├── configs/            pipeline configuration files
├── models/             future model artifacts
├── _design/            architecture and planning documents
├── README.md
└── LICENSE
```

## Current Project Status

The project is being developed in structured phases.

### Phase 1 - Pipeline Foundation

Complete:
- repository structure
- module architecture
- ingestion pipeline skeleton
- adapter schema mapping
- canonical schema definition

### Phase 2 - Data Validation

Complete:
- canonical record validation
- timestamp validation
- feature validation
- duplicate detection
- validation reporting
- quality reporting

### Phase 3 - Storage and Persistence

Complete at module level.

Implemented components:
- storage interface
- local file storage backend
- parquet storage backend
- storage configuration
- metadata tracking

Pipeline persistence integration occurs in Phase 4 orchestration work.

## Sample Data

The repository includes sample datasets used during development:
- opsight_sample_customers.json
- opsight_sample_events.parquet
- opsight_sample_finance.xlsx
- opsight_sample_sales.csv

These files simulate heterogeneous source systems for pipeline testing.

## Development Model

Development follows an issue-driven workflow.

Current storage-focused issue stream:
- PS-019 Storage Interface
- PS-020 Local File Storage
- PS-021 Parquet Storage Backend
- PS-022 Storage Configuration
- PS-023 Storage Factory
- PS-024 Persist Validated Records
- PS-025 Storage Error Handling
- PS-026 Storage Metadata Tracking

This approach keeps pipeline architecture aligned with implementation.

## License

This project is licensed under the MIT License.

See LICENSE for details.

## Status

Opsight is an experimental engineering project under active development.

Current phase summary:

- [x] Phase 1 complete
- [x] Phase 2 complete
- [x] Phase 3 persistence module complete
- [ ] Phase 4 pipeline orchestration
- [ ] Phase 5 API layer
- [ ] Phase 6 UI / visualization
- [ ] Phase 7 intelligence layer
- [ ] Phase 8 production readiness

The repository currently represents a functional ingestion, adapter, validation, and persistence module foundation. Future work focuses on orchestrating these modules end-to-end and then layering API and UI capabilities.
