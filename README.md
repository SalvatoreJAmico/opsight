# Opsight

Opsight is an experimental operational data pipeline for normalizing, validating, and preparing machine learning data from heterogeneous source systems.

## Current Scope

The repository currently contains the Phase 1 and Phase 2 foundation for the pipeline:

- ingestion record validation
- source format detection and canonical schema mapping
- canonical record validation and quality checks
- persistence scaffold for Phase 3

## Active Pipeline

The current module flow is:

```text
source data
	-> ingestion
	-> adapter
	-> validation
	-> persistence scaffold
```

## Repository Layout

- `modules/ingestion/` validates source records before they move into the pipeline.
- `modules/adapter/` detects source formats, loads datasets, and maps them into the canonical schema.
- `modules/validation/` validates canonical records and generates validation or quality reporting artifacts.
- `modules/persistence/` contains the Phase 3 storage scaffold.
- `_design/` contains architecture and planning documents.
- `data/` contains sample source files.

## Current Status

- Phase 1 foundation is complete.
- Phase 2 validation work is implemented.
- Phase 3 storage work has started with a scaffold and is not complete.

The project is under active development.