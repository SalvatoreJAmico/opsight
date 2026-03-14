from datetime import datetime


def validate_timestamp(timestamp):
    status = "valid"
    errors = []

    if timestamp is None:
        status = "invalid"
        errors.append("Missing timestamp")
    else:
        try:
            datetime.fromisoformat(timestamp)
        except (TypeError, ValueError):
            status = "invalid"
            errors.append("Invalid timestamp format")

    return {
        "status": status,
        "errors": errors,
    }