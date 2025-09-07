
from flask import request, current_app, abort
from werkzeug.exceptions import Unauthorized

from app.use_cases.manage_error_log import log_error_use_case


def validate_secret_token_clockify(webhook_type: str):
    """
    Valida el token del webhook de Clockify según el tipo de evento recibido.
    Los valores esperados deben estar definidos en el .env con claves como:
    - CLOCKIFY_SECRET_TOKEN_START
    - CLOCKIFY_SECRET_TOKEN_END
    - CLOCKIFY_SECRET_TOKEN_EDIT
    - CLOCKIFY_SECRET_TOKEN_DELETE
    - CLOCKIFY_SECRET_TOKEN_MANUAL_CREATE
    """
    token_map = {
        "start": "CLOCKIFY_SECRET_TOKEN_START",
        "end": "CLOCKIFY_SECRET_TOKEN_END",
        "edit": "CLOCKIFY_SECRET_TOKEN_EDIT",
        "delete": "CLOCKIFY_SECRET_TOKEN_DELETE",
        "manual_create": "CLOCKIFY_SECRET_TOKEN_MANUAL_CREATE"
    }

    try:
        config_key = token_map.get(webhook_type)
        if not config_key:
            raise ValueError(f"Unknown webhook type: {webhook_type}")

        received_token = request.headers.get("Clockify-Signature")
        expected_token = current_app.config.get(config_key)


        if not expected_token or received_token != expected_token:
            raise Unauthorized(f"Invalid token: {received_token}")

        return None
    except ValueError as e:
        log_error_use_case(
            endpoint="validate_token_clockify",
            method="SYSTEM",
            error=e,
            payload={
                "webhook_type": webhook_type
            },
            response_code=400
        )
        abort(400, description=str(e))
    except Unauthorized as e:
        log_error_use_case(
            endpoint="validate_token_clockify",
            method="SYSTEM",
            error=e,
            payload={
                "webhook_type": webhook_type,
                "received_token": request.headers.get("X-Webhook-Token")
            },
            response_code=401
        )
        raise e