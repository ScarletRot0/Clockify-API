from flask import Blueprint, request, jsonify
from werkzeug.exceptions import BadRequest

from app.use_cases.manage_sessions_binnacle import (
    create_session_binnacle_use_case,
    list_session_binnacles_use_case,
    get_session_binnacle_use_case,
    get_session_binnacles_by_session_use_case, search_session_binnacles_use_case
)
from app.use_cases.validate_token import validate_secret_token

binnacle_bp = Blueprint("session_binnacles", __name__, url_prefix="/api-clockify/session-binnacle")

@binnacle_bp.route("/getAll/", methods=["GET"])
def list_binnacles():
    token_error = validate_secret_token()
    if token_error:
        return token_error
    try:
        return list_session_binnacles_use_case()
    except Exception as e:
        return jsonify({"error": f"Internal server error {str(e)}"}), 500

@binnacle_bp.route("/getById/<int:id_binnacle>", methods=["GET"])
def get_binnacle(id_binnacle):
    token_error = validate_secret_token()
    if token_error:
        return token_error
    try:
        if not id_binnacle:
            raise BadRequest("id_binnacle argument is required.")
        return get_session_binnacle_use_case(id_binnacle)
    except LookupError as e:
        return jsonify({"error": str(e)}), 404

    except BadRequest as e:
        return jsonify({"error": str(e)}), 400

    except Exception as e:
        return jsonify({"error": f"Internal server error {str(e)}"}), 500

@binnacle_bp.route("/getByIdSession/<int:id_sesion>", methods=["GET"])
def get_binnacles_by_session(id_sesion):
    token_error = validate_secret_token()
    if token_error:
        return token_error
    try:
        if not id_sesion:
            raise BadRequest("id_sesion argument is required.")
        return get_session_binnacles_by_session_use_case(id_sesion)
    except LookupError as e:
        return jsonify({"error": str(e)}), 404

    except BadRequest as e:
        return jsonify({"error": str(e)}), 400

    except Exception as e:
        return jsonify({"error": f"Internal server error {str(e)}"}), 500

@binnacle_bp.route("/create/", methods=["POST"])
def create_binnacle():
    token_error = validate_secret_token()
    if token_error:
        return token_error
    try:
        return create_session_binnacle_use_case(request.get_json())
    except BadRequest as e:
        return jsonify({"error": str(e)}), 400
    except ValueError as e:
        return jsonify({"error": str(e)}), 422
    except Exception as e:
        return jsonify({"error": f"Internal server error {str(e)}"}), 500


@binnacle_bp.route("/search/", methods=["GET"])
def search_binnacles():
    token_error = validate_secret_token()
    if token_error:
        return token_error
    try:
        return search_session_binnacles_use_case(request.args)
    except LookupError as e:
        return jsonify({"error": str(e)}), 404
    except BadRequest as e:
        return jsonify({"error": str(e)}), 400
    except ValueError as e:
        return jsonify({"error": str(e)}), 422
    except Exception as e:
        return jsonify({"error": f"Internal server error {str(e)}"}), 500
