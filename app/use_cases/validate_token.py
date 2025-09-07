from flask import request, current_app, abort
from werkzeug.exceptions import Unauthorized
from app.use_cases.manage_error_log import log_error_use_case


def validate_secret_token():
    try:
        received_token = request.headers.get("X-Webhook-Token")
        expected_token = current_app.config.get("SECRET_TOKEN")
        if not expected_token or received_token != expected_token:
            raise Unauthorized(f"error: Unauthorized")
        return None  # significa que ta todo bien

    except Unauthorized as e:
        log_error_use_case(
            endpoint="validate_token",
            method="SYSTEM",
            error=e,
            payload={
                "received_token": request.headers.get("X-Webhook-Token")
            },
            response_code=401
        )
        abort(401, description=str(e))

