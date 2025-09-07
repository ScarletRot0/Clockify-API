import traceback
from datetime import datetime, UTC


def map_exception_to_error_log_data(
    endpoint: str,
    method: str,
    error: Exception,
    payload: dict,
    response_code: int,
    id_user: int = None,
    external_user_id: str = None
):
    # Normalizar payload si es str o cualquier tipo incorrecto
    if not isinstance(payload, dict):
        payload = {"message": str(payload)}

    # Extraer datos del usuario si existen y son dict
    user_data = payload.get("user", {})
    if not isinstance(user_data, dict):
        user_data = {}

    enable = user_data.get("ACTIVE", True)
    disable_time = None
    if not enable:
        disable_time = datetime.now(UTC)

    return {
        "endpoint": endpoint,
        "method": method,
        "errorMessage": str(error),
        "stackTrace": traceback.format_exc(),
        "payload": payload,
        "responseCode": response_code,
        "createdAt": datetime.now(UTC),
        "idUser": id_user,
        "externalUserId": external_user_id,
        "enable": enable,
        "disableTime": disable_time
    }