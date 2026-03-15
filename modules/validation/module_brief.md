# Validation Module

## Purpose

Validate canonical records before they move further in the pipeline and produce quality reporting for downstream review.

## Responsibilities

- verify required canonical fields
- validate feature payload shape
- validate timestamp formatting
- validate record batches
- detect duplicate entity and timestamp combinations
- generate validation summary and quality reports

## Current Status

Phase 2 validation scope is complete, including validation tests in `tests/test_validation.py`.

## Current Files

- `validator.py` for record-level canonical validation
- `batch_validator.py` for aggregate batch validation
- `timestamp_validation.py` for timestamp checks
- `feature_validation.py` for feature payload checks
- `duplicate_check.py` for duplicate detection
- `report.py` for validation summary report generation
- `quality_report.py` for quality report generation