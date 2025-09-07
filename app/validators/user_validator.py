def validate_user_data(data, is_update=False):
    errors = []

    if not is_update:
        if not data.get("ExternalUserId"):
            errors.append("User 'ExternalUserId' is required")
        if not data.get("name"):
            errors.append("User 'name' is required")

    if "hoursPerMonth" in data and not isinstance(data["hoursPerMonth"], int):
        errors.append("'hoursPerMonth' must be an integer")

    if "enable" in data and not isinstance(data["enable"], bool):
        errors.append("'enable' must be a boolean")

    if "notify" in data and not isinstance(data["notify"], bool):
        errors.append("'notify' must be a boolean")

    return len(errors) == 0, errors