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

    if record.get("entity_id") is None:
        validation_report["status"] = "invalid"
        validation_report["errors"].append("Missing entity_id")

    if record.get("timestamp") is None:
        validation_report["status"] = "invalid"
        validation_report["errors"].append("Missing timestamp")

    if record.get("features") is None:
        validation_report["status"] = "invalid"
        validation_report["errors"].append("Missing features")
    elif not isinstance(record.get("features"), dict):
        validation_report["status"] = "invalid"
        validation_report["errors"].append("Features must be a dictionary")

    if record.get("metadata") is None:
        validation_report["status"] = "invalid"
        validation_report["errors"].append("Missing metadata")

    return validation_report
