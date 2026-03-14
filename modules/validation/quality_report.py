def generate_validation_report(validation_results):

    report = {
        "dataset_status": validation_results["status"],
        "records_processed": validation_results["total_records"],
        "valid_records": validation_results["valid_records"],
        "invalid_records": validation_results["invalid_records"],
        "errors": validation_results["results"]
    }

    return report


def generate_quality_report(validation_report, duplicate_results):

    report = {
        "pipeline_stage": "validation",
        "dataset_status": validation_report["dataset_status"],
        "summary": {
            "records_processed": validation_report["records_processed"],
            "valid_records": validation_report["valid_records"],
            "invalid_records": validation_report["invalid_records"],
            "duplicate_records": len(duplicate_results["duplicate_records"])
        },
        "errors": validation_report["errors"],
        "warnings": []
    }

    if duplicate_results["duplicates_found"]:
        report["warnings"].append("Duplicate records detected")

    return report