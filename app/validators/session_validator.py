def validate_session_data(data, is_update=False):
    errors = []

    required_fields = [
        "external_sesion_id", "description", "idUser", "idProject", "projectName",
        "idWorkspace", "workspaceName", "idTask", "taskName", "startDate"
    ]

    #Solo validar requeridos si no es update
    if not is_update:
        for field in required_fields:
            if not data.get(field):
                errors.append(f"'{field}' is required")

    #validaciones condicionales
    if "endDate" in data and data["endDate"] is not None:
        if not isinstance(data["endDate"], str):  # puedes hacer validación de fecha también si quieres
            errors.append("'endDate' must be a string (ISO datetime) if provided")

    if "duration" in data and data["duration"] is not None:
        if not isinstance(data["duration"], (str, int, float)):  # depende de cómo lo manejes en el mapper
            errors.append("'duration' must be a valid duration type if provided")

    if "offsetStart" in data and not isinstance(data["offsetStart"], int):
        errors.append("'offsetStart' must be an integer")

    if "offsetEnd" in data and data["offsetEnd"] is not None:
        if not isinstance(data["offsetEnd"], int):
            errors.append("'offsetEnd' must be an integer if provided")

    if "currentlyRunning" in data and not isinstance(data["currentlyRunning"], bool):
        errors.append("'currentlyRunning' must be a boolean")

    if "enable" in data and not isinstance(data["enable"], bool):
        errors.append("'enable' must be a boolean")

    if "updatingQuantity" in data and not isinstance(data["updatingQuantity"], int):
        errors.append("'updatingQuantity' must be an integer")

    return len(errors) == 0, errors