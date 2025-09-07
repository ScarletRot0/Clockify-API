from flask import Blueprint, request, jsonify
from werkzeug.exceptions import BadRequest

from app.use_cases.process_webhook import process_webhook_use_case
from app.use_cases.validate_token import validate_secret_token
from app.use_cases.validate_token_clockify import validate_secret_token_clockify
from app.use_cases.webhook_session_start import handle_session_start_use_case
from app.use_cases.webhook_session_end import handle_session_end_use_case
from app.use_cases.webhook_session_delete import handle_session_delete_use_case
from app.services.mail_service_manual import send_webhook_email
from app.use_cases.webhook_session_manual import handle_session_manual_creation_use_case
import json

#Pasar a un controlador a parte
webhook_bp = Blueprint("webhook", __name__, url_prefix='/api-clockify/webhook')

@webhook_bp.route("/edit", methods=["POST"])
def handle_webhook():
    auth_error = validate_secret_token_clockify("edit")
    if auth_error:
        return auth_error
    try:
        data = request.get_json()
        if not data:
            raise BadRequest("JSON body is required.")

        result = process_webhook_use_case(data)
        return jsonify(result), 200

    except ValueError as e:
        return jsonify({"error": str(e)}), 422

    except BadRequest as e:
        return jsonify({"error": str(e)}), 400

    except Exception as e:
        return jsonify({"error": f"Internal server error {str(e)}"}), 500

@webhook_bp.route("/start", methods=["POST"])
def handle_webhook_start():
    auth_error = validate_secret_token_clockify("start")
    if auth_error:
        return auth_error
    try:
        data = request.get_json()
        if not data:
            raise BadRequest("JSON body is required.")

        result = handle_session_start_use_case(data)
        return jsonify(result), 200

    except ValueError as e:
        return jsonify({"error": str(e)}), 422

    except BadRequest as e:
        return jsonify({"error": str(e)}), 400

    except Exception as e:
        return jsonify({"error": f"Internal server error {str(e)}"}), 500

@webhook_bp.route("/end", methods=["POST"])
def handle_webhook_end():
    auth_error = validate_secret_token_clockify("end")
    if auth_error:
        return auth_error
    try:
        data = request.get_json()
        if not data:
            raise BadRequest("JSON body is required.")

        result = handle_session_end_use_case(data)
        return jsonify(result), 200

    except ValueError as e:
        return jsonify({"error": str(e)}), 422

    except BadRequest as e:
        return jsonify({"error": str(e)}), 400

    except LookupError as e:
        return jsonify({"error": str(e)}), 404

    except Exception as e:
        return jsonify({"error": f"Internal server error {str(e)}"}), 500

@webhook_bp.route("/delete", methods=["POST"])
def handle_webhook_delete():
    auth_error = validate_secret_token_clockify("delete")
    if auth_error:
        return auth_error
    try:
        data = request.get_json()
        if not data:
            raise BadRequest("JSON body is required.")

        result = handle_session_delete_use_case(data)
        return jsonify(result), 200

    except ValueError as e:
        return jsonify({"error": str(e)}), 422

    except LookupError as e:
        return jsonify({"error": str(e)}), 404

    except BadRequest as e:
        return jsonify({"error": str(e)}), 400

    except Exception as e:
        return jsonify({"error": f"Internal server error {str(e)}"}), 500

@webhook_bp.route("/manual", methods=["POST"])
def handle_webhook_manual():
    auth_error = validate_secret_token_clockify("manual_create")
    if auth_error:
        return auth_error
    try:
        data = request.get_json()
        if not data:
            raise BadRequest("JSON body is required.")

        result = handle_session_manual_creation_use_case(data)
        return jsonify(result), 200

    except ValueError as e:
        return jsonify({"error": str(e)}), 422

    except BadRequest as e:
        return jsonify({"error": str(e)}), 400

    except Exception as e:
        return jsonify({"error": f"Internal server error {str(e)}"}), 500


@webhook_bp.route("/test-email", methods=["GET"])
def test_email():
    token_error = validate_secret_token()
    if token_error:
        return token_error
    test_data = {
        "description": "Prueba de actividad",
        "user": "juan@example.com",
        "start": "2025-06-05T09:00:00Z",
        "end": "2025-06-05T11:00:00Z",
        "project": "Web Development"
    }
    subject = "Test Webhook Email"
    body = json.dumps(test_data, indent=2)

    try:
        send_webhook_email(subject, body)
        return jsonify({"status": "Test email sent"}), 200
    except Exception as e:
        return jsonify({"error": f"Internal server error {str(e)}"}), 500
