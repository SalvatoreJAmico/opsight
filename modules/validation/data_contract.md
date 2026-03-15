# Validation Data Contract

This module validates canonical records produced by the adapter module.

Expected record structure:

- entity_id
- timestamp
- features
- metadata

Record-level validation is implemented in `validator.py` via `validate_canonical_record(record)`.

Invalid records return a validation error object.

The validation module returns a dictionary with the following fields:

status
    Indicates whether the record passed validation.
    Possible values:
        valid
        invalid

errors
    A list of validation error messages.
    Empty if the record is valid.

{
  "status": "valid",
  "errors": []
}

{
  "status": "invalid",
  "errors": [
      "Missing entity_id",
      "Features must be a dictionary"
  ]
}

`errors` may include:

- Missing entity_id
- Missing timestamp
- Missing features
- Features must be a dictionary
- Missing metadata

## Batch Validation Output

Batch validation returns aggregate validation results using this structure:

```json
{
  "status": "valid",
  "total_records": 10,
  "valid_records": 10,
  "invalid_records": 0,
  "results": []
}
```

If invalid records are present, `results` contains per-record error entries.

## Duplicate Validation Output

Duplicate detection is implemented in `duplicate_check.py` with `detect_duplicates(records)`.

```json
{
  "duplicates_found": true,
  "duplicate_records": [
    {
      "record_index": 1,
      "entity_id": "cust-001",
      "timestamp": "2026-03-15T12:00:00"
    }
  ]
}
```

Duplicates are identified by the `(entity_id, timestamp)` pair.

## Timestamp and Feature Validation

- `timestamp_validation.py` exposes `validate_timestamp(timestamp)` and returns `{ "status": "valid|invalid", "errors": [] }`.
- `feature_validation.py` exposes `validate_features(features)` and returns `{ "status": "valid|invalid", "errors": [] }`.

## Validation Summary Output

Validation summary reporting is generated in `report.py` with this structure:

```json
{
  "dataset_status": "valid",
  "records_processed": 10,
  "valid_records": 10,
  "invalid_records": 0,
  "errors": []
}
```

## Quality Reporting Output

Quality reporting is generated in `quality_report.py` and remains separate from validation summary reporting.

Quality reports use this structure:

```json
{
  "pipeline_stage": "validation",
  "dataset_status": "valid",
  "summary": {
    "records_processed": 10,
    "valid_records": 10,
    "invalid_records": 0,
    "duplicate_records": 0
  },
  "errors": [],
  "warnings": []
}
```