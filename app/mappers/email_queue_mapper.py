from datetime import datetime, UTC


def map_email_to_queue_entity(to_address, subject, body, attachments=None):
    return {
        "toAddress": to_address,
        "subject": subject,
        "body": body,
        "status": 0,
        "retries": 0,
        "attachments": attachments or [],
        "createdAt": datetime.now(UTC)
    }