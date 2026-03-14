def generate_validation_report(validation_results):

    report = {
        "dataset_status": validation_results["status"],
        "records_processed": validation_results["total_records"],
        "valid_records": validation_results["valid_records"],
        "invalid_records": validation_results["invalid_records"],
        "errors": validation_results["results"]
    }

    return report