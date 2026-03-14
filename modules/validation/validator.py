def validate_canonical_record(record):

    # This function validates a record against the Opsight canonical schema. It checks for the presence of required fields and ensures that the features field is a dictionary. The function returns a validation report indicating whether the record is valid or invalid, along with any errors found during validation.

    if not isinstance(record, dict):
        return {
            "status": "invalid",
            "errors": ["Record must be a dictionary"]
        }
    
    validation_report = {
        "status": "valid",
        "errors": []
    }
    
    if "entity_id" not in record or record["entity_id"] is None:
        validation_report["status"] = "invalid"
        validation_report["errors"].append("Missing entity_id")
        
    if "timestamp" not in record or record.get("timestamp") is None:

        validation_report["status"] = "invalid"
        validation_report["errors"].append("Missing timestamp")

    if "features" not in record or record.get("features") is None:
        validation_report["status"] = "invalid"
        validation_report["errors"].append("Missing features")
    else: 
        if not isinstance(record.get("features"), dict):
            validation_report["status"] = "invalid"
            validation_report["errors"].append("Features must be a dictionary")

    if "metadata" not in record or record["metadata"] is None:
        validation_report["status"] = "invalid"
        validation_report["errors"].append("Missing metadata")
    
    return validation_report
