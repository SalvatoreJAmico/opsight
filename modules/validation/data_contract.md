# Validation Data Contract

This module validates canonical records.

Expected record structure:

- entity_id
- timestamp
- features
- metadata

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