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

## Output Contract

Phase 3 will define the durable storage output format. For now, the module exposes a storage entry point and does not yet return persisted record metadata.

## Notes

- input records should already have passed validation
- persistence backends may include files, databases, or services in later work