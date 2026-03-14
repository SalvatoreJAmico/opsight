def validate_features(features):
    status = "valid"
    errors = []

    if features is None:
        status = "invalid"
        errors.append("Missing features")

    elif not isinstance(features, dict):
        status = "invalid"
        errors.append("Features must be a dictionary")

    else:
        for key, value in features.items():
            if value is None:
                status = "invalid"
                errors.append(f"Feature '{key}' is missing a value")

    return {
        "status": status,
        "errors": errors
    }
