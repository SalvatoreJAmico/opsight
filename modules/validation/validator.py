import pandas as pd
from pandas.api.types import is_scalar


def _is_missing_scalar(value):
    """Recognize scalar nulls without testing containers for truthiness.

    pandas string/datetime columns may expose NaN, NA, or NaT rather
    than None. Container validation remains the caller's responsibility.
    """
    return is_scalar(value) and bool(pd.isna(value))


def validate_canonical_record(record):
    if not isinstance(record, dict):
        return {
            "status": "invalid",
            "errors": ["Record must be a dictionary"],
        }

    validation_report = {
        "status": "valid",
        "errors": [],
    }

    if _is_missing_scalar(record.get("entity_id")):
        validation_report["status"] = "invalid"
        validation_report["errors"].append("Missing entity_id")

    if _is_missing_scalar(record.get("timestamp")):
        validation_report["status"] = "invalid"
        validation_report["errors"].append("Missing timestamp")

    if _is_missing_scalar(record.get("features")):
        validation_report["status"] = "invalid"
        validation_report["errors"].append("Missing features")
    elif not isinstance(record.get("features"), dict):
        validation_report["status"] = "invalid"
        validation_report["errors"].append("Features must be a dictionary")

    if _is_missing_scalar(record.get("metadata")):
        validation_report["status"] = "invalid"
        validation_report["errors"].append("Missing metadata")

    return validation_report
