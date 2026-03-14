def generate_validation_report(validation_results):
    return {
        "dataset_status": validation_results.get("status", "invalid"),
        "records_processed": validation_results.get("total_records", 0),
        "valid_records": validation_results.get("valid_records", 0),
        "invalid_records": validation_results.get("invalid_records", 0),
        "errors": validation_results.get("results", []),
    }