# Persistence Data Contract

## Purpose

The persistence module accepts validated canonical records and stores them in a durable backend.

## Input Contract

The current expected input is a list of validated canonical records.

```json
[
  {
    "entity_id": "customer-101",
    "timestamp": "2026-03-13T10:00:00",
    "features": {
      "amount": 45.0,
      "region": "west"
    },
    "metadata": {}
  }
]
```

Validation expectation:

- records should already be validated by the validation module
- each record should include `entity_id`, `timestamp`, `features`, and `metadata`

## Output Contract

The persistence interface exposes two operations:

- `save_records(records)` persists records and returns `None`
- `load_records()` returns a list of canonical records

Backend behavior:

- JSON backend (`local_storage.py`) writes to `data/records.json`
- Parquet backend (`parquet_storage.py`) writes to `data/records.parquet`

`persistence_manager.py` delegates persistence through the backend selected by `storage_factory.py`.

## Notes

- input records should already have passed validation
- current supported backends are `json` and `parquet`
- full pipeline orchestration wiring occurs in Phase 4