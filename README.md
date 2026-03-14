Opsight

Opsight is an experimental operational data pipeline for ingesting, normalizing, validating, and preparing structured data for analytics and machine learning workflows.

The system is designed as a modular pipeline architecture, allowing new data sources, validation rules, and storage backends to be added without modifying the core pipeline.

Pipeline Overview

Opsight processes data through a sequence of modular stages.

source data
    -> ingestion
    -> adapter
    -> validation
    -> persistence
Ingestion

Reads raw datasets from heterogeneous source systems and prepares them for pipeline processing.

Responsibilities:

detect source file formats

load datasets from disk

perform basic source record validation

Adapter

Transforms source records into the Opsight canonical schema.

Responsibilities:

normalize source records

map heterogeneous schemas to canonical format

enforce canonical record structure

Validation

Validates canonical records and produces quality reporting artifacts.

Responsibilities:

canonical schema validation

timestamp validation

feature validation

duplicate detection

validation summary reporting

quality report generation

Persistence

Stores validated records using configurable storage backends.

Responsibilities:

abstract storage interface

local file storage

parquet storage backend

storage configuration and metadata tracking

Persistence is currently under development.

Canonical Record Structure

Records within the pipeline follow a canonical schema.

{
    "entity_id": str,
    "timestamp": str,
    "features": dict,
    "metadata": dict
}

This schema provides a consistent structure for validation and downstream analytics workflows.

Repository Layout
opsight/
│
├── modules/
│   ├── ingestion/
│   │   ├── ingestion.py
│   │   ├── data_contract.md
│   │   └── module_brief.md
│   │
│   ├── adapter/
│   │   ├── adapter.py
│   │   ├── data_contract.md
│   │   └── module_brief.md
│   │
│   ├── validation/
│   │   ├── validator.py
│   │   ├── batch_validator.py
│   │   ├── timestamp_validation.py
│   │   ├── feature_validation.py
│   │   ├── duplicate_check.py
│   │   ├── quality_report.py
│   │   ├── data_contract.md
│   │   └── module_brief.md
│   │
│   └── persistence/
│       └── storage.py
│
├── data/               sample source datasets
├── notebooks/          experimentation notebooks
├── reports/            generated pipeline reports
├── configs/            pipeline configuration files
├── models/             future model artifacts
│
├── _design/            architecture and planning documents
├── README.md
└── LICENSE
Current Project Status

The project is currently being developed in structured phases.

Phase 1 — Pipeline Foundation

Complete

repository structure

module architecture

ingestion pipeline skeleton

adapter schema mapping

canonical schema definition

Phase 2 — Data Validation

Complete

canonical record validation

timestamp validation

feature validation

duplicate detection

validation reporting

quality reporting

Phase 3 — Storage & Persistence

In progress

Planned components:

storage interface

local file storage backend

parquet storage backend

storage configuration

metadata tracking

pipeline persistence integration

Sample Data

The repository includes sample datasets used during development:

opsight_sample_customers.json
opsight_sample_events.parquet
opsight_sample_finance.xlsx
opsight_sample_sales.csv

These files simulate heterogeneous source systems for pipeline testing.

Development Model

Development follows an issue-driven workflow.

Each feature is implemented through a structured issue process:

PS-019 Storage Interface
PS-020 Local File Storage
PS-021 Parquet Storage Backend
PS-022 Storage Configuration
PS-023 Storage Factory
PS-024 Persist Validated Records
PS-025 Storage Error Handling
PS-026 Storage Metadata Tracking

This approach keeps pipeline architecture aligned with implementation.

License

This project is licensed under the MIT License.

See the LICENSE file for details.

Status

Opsight is an experimental engineering project under active development.

The repository currently represents a functional validation pipeline and the foundation for a modular operational data processing system.

Future work will expand persistence, pipeline orchestration, and analytics capabilities.
