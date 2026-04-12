import pandas as pd


def _is_missing(value) -> bool:
    if value is None:
        return True
    try:
        return bool(pd.isna(value))
    except Exception:
        return False


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

    if _is_missing(record.get("entity_id")):
        validation_report["status"] = "invalid"
        validation_report["errors"].append("Missing entity_id")

    if _is_missing(record.get("timestamp")):
        validation_report["status"] = "invalid"
        validation_report["errors"].append("Missing timestamp")

    if _is_missing(record.get("features")):
        validation_report["status"] = "invalid"
        validation_report["errors"].append("Missing features")
    elif not isinstance(record.get("features"), dict):
        validation_report["status"] = "invalid"
        validation_report["errors"].append("Features must be a dictionary")

    if _is_missing(record.get("metadata")):
        validation_report["status"] = "invalid"
        validation_report["errors"].append("Missing metadata")

    return validation_report
