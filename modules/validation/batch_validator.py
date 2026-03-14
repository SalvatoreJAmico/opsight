
from .validator import validate_canonical_record


def validate_batch(records):
    status = "valid"
    total = 0
    valid = 0
    invalid = 0
    results = []

    for index, record in enumerate(records):
        total += 1
        result = validate_canonical_record(record)

        if result.get("status") == "invalid":
            invalid += 1
            results.append({
                "record_index": index,
                "errors": result.get("errors", []),
            })
        else:
            valid += 1

    if invalid > 0:
        status = "invalid"

    validation_results = {
        "status": status,
        "total_records": total,
        "valid_records": valid,
        "invalid_records": invalid,
        "results": results,
    }

    return validation_results
