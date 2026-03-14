def generate_quality_report(validation_report, duplicate_results):
    report = {
        "pipeline_stage": "validation",
        "dataset_status": validation_report.get("dataset_status", "invalid"),
        "summary": {
            "records_processed": validation_report.get("records_processed", 0),
            "valid_records": validation_report.get("valid_records", 0),
            "invalid_records": validation_report.get("invalid_records", 0),
            "duplicate_records": len(duplicate_results.get("duplicate_records", [])),
        },
        "errors": validation_report.get("errors", []),
        "warnings": [],
    }

    if duplicate_results.get("duplicates_found", False):
        report["warnings"].append("Duplicate records detected")

    return report