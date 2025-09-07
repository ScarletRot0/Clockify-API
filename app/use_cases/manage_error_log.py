from app.mappers.error_log_mapper import map_exception_to_error_log_data
from app.validators.error_log_validator import validate_error_log_data
from app.repositories.error_log_repository import create_error_log
from app.models.user import User

def log_error_use_case(
    endpoint: str,
    method: str,
    error: Exception,
    payload: dict,
    response_code: int
):
    if not isinstance(payload, dict):
        payload = {"message": str(payload)}

    external_user_id = None
    id_user = None

    #  extraer external_user_id desde payload["user"] si es un dict
    user_data = payload.get("user")
    if isinstance(user_data, dict):
        external_user_id = user_data.get("id")

        # id_user en la base de datos si se tiene external_user_id
        if external_user_id:
            user = User.query.filter_by(external_user_id=external_user_id).first()
            if user:
                id_user = user.id

    # Mapea los datos del error
    error_data = map_exception_to_error_log_data(
        endpoint=endpoint,
        method=method,
        error=error,
        payload=payload,
        response_code=response_code,
        id_user=id_user,
        external_user_id=external_user_id
    )

    is_valid, errors = validate_error_log_data(error_data)
    if not is_valid:
        return {"message": "Invalid error log data", "errors": errors}

    return create_error_log(error_data)
