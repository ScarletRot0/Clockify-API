def validate_approve_session_data(data):
    errors = []

    # Campo requerido: aprobado (bool)
    if "aprobado" not in data:
        errors.append("'aprobado' es requerido")
    elif not isinstance(data["aprobado"], bool):
        errors.append("'aprobado' debe ser de tipo booleano")

    # Campo requerido: observacion (string, max 500 caracteres)
    if "observacion" not in data:
        errors.append("'observacion' es requerido")
    elif not isinstance(data["observacion"], str):
        errors.append("'observacion' debe ser una cadena de texto")
    elif len(data["observacion"]) > 500:
        errors.append("'observacion' no puede superar los 500 caracteres")

    return len(errors) == 0, errors