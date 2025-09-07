from datetime import datetime
from flask import jsonify

def parse_date_param(raw_date, param_name):
    if not raw_date:
        return None, None

    accepted_formats = [
        "%Y-%m-%d",        # estandar: 2025-07-01
        "%Y-%d-%m",        # posible confusion: 2025-01-07
        "%m-%d-%Y",        # formato americano: 07-01-2025
        "%d-%m-%Y",        # formato latino: 01-07-2025
        "%Y-%m-%dT%H:%M:%S",  # ISO datetime
        "%Y-%m-%dT%H:%M:%S.%f",  # ISO datetime con milisegundos
    ]

    for fmt in accepted_formats:
        try:
            parsed = datetime.strptime(raw_date, fmt)
            return parsed.date().isoformat(), None
        except ValueError:
            continue

    #si ninguna funciona:
    return None, (
        jsonify({
            "error": f"Invalid date format for '{param_name}'",
            "expectedFormats": [
                "YYYY-MM-DD", "YYYY-DD-MM", "MM-DD-YYYY", "DD-MM-YYYY", "ISO 8601"
            ],
            "received": raw_date
        }), 400
    )
