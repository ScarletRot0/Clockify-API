def validate_error_log_data(data):
    errors = []

    required_fields = [
        "endpoint",
        "method",
        "errorMessage",
        "responseCode"
    ]

    for field in required_fields:
        if not data.get(field):
            errors.append(f"'{field}' is required")

    if "responseCode" in data and not isinstance(data["responseCode"], int):
        errors.append("'responseCode' must be an integer")

    if "enable" in data and not isinstance(data["enable"], bool):
        errors.append("'enable' must be a boolean")

    return len(errors) == 0, errors