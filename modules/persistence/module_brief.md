# Persistence Module

## Purpose

Store validated canonical records and establish the persistence boundary for the Opsight pipeline.

## Responsibilities

- accept validated canonical records
- save and load records through a storage interface
- provide JSON and Parquet storage backends
- select backends through the storage factory
- expose persistence manager entry points for pipeline orchestration

## Current Status

Storage module and persistence backends are implemented.

- `storage_interface.py` defines `save_records(records)` and `load_records()`.
- `local_storage.py` persists canonical records as JSON.
- `parquet_storage.py` persists canonical records as Parquet.
- `storage_factory.py` selects the backend from config (`json` or `parquet`).
- `persistence_manager.py` delegates persistence through the selected backend.

Full pipeline integration occurs in Phase 4 orchestration work.