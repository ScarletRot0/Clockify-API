def validate_email_queue_data(data):
    errors = []

    if not data.get("toAddress"):
        errors.append("'toAddress' is required")
    if not data.get("subject"):
        errors.append("'subject' is required")
    if not data.get("body"):
        errors.append("'body' is required")

    return len(errors) == 0, errors