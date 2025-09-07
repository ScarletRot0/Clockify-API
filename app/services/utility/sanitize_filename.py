import re
def sanitize_filename(value: str) -> str:
    return re.sub(r'[^a-zA-Z0-9_\-]', '_', value.strip().lower())