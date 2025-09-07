def validate_session_binnacle_data(data):
    errors = []

    required_fields = [
        "external_sesion_id", "description", "idUser", "idSesion",
        "idProject", "projectName", "idWorkspace", "workspaceName",
        "idTask", "taskName", "startDate", "timeZone"
    ]

    for field in required_fields:
        if not data.get(field):
            errors.append(f"'{field}' is required")

    #validacion condicional de campos opcionales que pueden ser nulos
    if "endDate" in data and data["endDate"] is not None:
        if not isinstance(data["endDate"], str):  # o validar ISO string si deseas
            errors.append("'endDate' must be a string (ISO format) if provided")

    if "duration" in data and data["duration"] is not None:
        if not isinstance(data["duration"], (str, int, float)):
            errors.append("'duration' must be a valid duration type if provided")

    if "offsetStart" in data and not isinstance(data["offsetStart"], int):
        errors.append("'offsetStart' must be an integer")

    if "offsetEnd" in data and data["offsetEnd"] is not None:
        if not isinstance(data["offsetEnd"], int):
            errors.append("'offsetEnd' must be an integer if provided")

    if "enable" in data and not isinstance(data["enable"], bool):
        errors.append("'enable' must be a boolean")

    if "updatingQuantity" in data and not isinstance(data["updatingQuantity"], int):
        errors.append("'updatingQuantity' must be an integer")

    return len(errors) == 0, errors