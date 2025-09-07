from flask import Blueprint, request, jsonify
from app.use_cases.approve_session_use_case import approve_session_use_case
from app.use_cases.manage_sessions import (
    list_sessions_use_case,
    get_session_by_id_use_case,
    get_session_by_id_user_use_case,
    get_session_by_email_user_use_case,
    create_session_use_case,
    update_session_use_case,
    delete_session_use_case
)
from app.use_cases.manage_sessions import search_sessions_use_case
from app.use_cases.validate_token import validate_secret_token
from werkzeug.exceptions import BadRequest
session_bp = Blueprint('sessions', __name__, url_prefix='/api-clockify/sessions')


@session_bp.route('/getAll', methods=['GET'])
def index():
    token_error = validate_secret_token()
    if token_error:
        return token_error
    try:
        return jsonify(list_sessions_use_case()), 200
    except Exception as e:
        return jsonify({"error": f"Internal server error {str(e)}"}), 500

@session_bp.route('/getById/<int:session_id>', methods=['GET'])
def show(session_id):
    token_error = validate_secret_token()
    if token_error:
        return token_error
    try:
        if not session_id:
            raise BadRequest("session id is required.")

        return jsonify(get_session_by_id_use_case(session_id)), 200

    except LookupError as e:
        return jsonify({"error": str(e)}), 404

    except BadRequest as e:
        return jsonify({"error": str(e)}), 400

    except Exception as e:
        return jsonify({"error": f"Internal server error {str(e)}"}), 500

@session_bp.route('/getByUser/<int:user_id>', methods=['GET'])
def show_by_user_id(user_id):
    token_error = validate_secret_token()
    if token_error:
        return token_error
    try:
        if not user_id:
            raise BadRequest("user id is required.")

        return get_session_by_id_user_use_case(user_id)

    except LookupError as e:
        return jsonify({"error": str(e)}), 404

    except BadRequest as e:
        return jsonify({"error": str(e)}), 400

    except Exception as e:
        return jsonify({"error": f"Internal server error {str(e)}"}), 500

@session_bp.route('/getByEmail/<string:email>', methods=['GET'])
def show_by_user_email(email):
    token_error = validate_secret_token()
    if token_error:
        return token_error
    try:
        if not email:
            raise BadRequest("email is required.")

        return get_session_by_email_user_use_case(email)

    except LookupError as e:
        return jsonify({"error": str(e)}), 404

    except BadRequest as e:
        return jsonify({"error": str(e)}), 400

    except Exception as e:
        return jsonify({"error": f"Internal server error {str(e)}"}), 500

@session_bp.route('/create', methods=['POST'])
def create():
    token_error = validate_secret_token()
    if token_error:
        return token_error
    try:
        data = request.get_json()
        if not data:
            raise BadRequest("JSON body is required.")

        return create_session_use_case(request.get_json())

    except ValueError as e:
        return jsonify({"error": str(e)}), 422

    except BadRequest as e:
        return jsonify({"error": str(e)}), 400

    except Exception as e:
        return jsonify({"error": f"Internal server error {str(e)}"}), 500

@session_bp.route('/update/<int:session_id>', methods=['PUT'])
def update(session_id):
    token_error = validate_secret_token()
    if token_error:
        return token_error

    try:
        data = request.get_json()
        if not data or not session_id:
            raise BadRequest("JSON body or session id is required.")

        return update_session_use_case(session_id, request.get_json())

    except ValueError as e:
        return jsonify({"error": str(e)}), 422

    except LookupError as e:
        return jsonify({"error": str(e)}), 404

    except BadRequest as e:
        return jsonify({"error": str(e)}), 400

    except Exception as e:
        return jsonify({"error": f"Internal server error {str(e)}"}), 500

@session_bp.route('/delete/<int:session_id>', methods=['DELETE'])
def delete(session_id):
    token_error = validate_secret_token()
    if token_error:
        return token_error
    try:
        if not session_id:
            raise BadRequest("session id is required.")

        return delete_session_use_case(session_id)

    except LookupError as e:
        return jsonify({"error": str(e)}), 404

    except BadRequest as e:
        return jsonify({"error": str(e)}), 400

    except Exception as e:
        return jsonify({"error": f"Internal server error {str(e)}"}), 500

@session_bp.route("/search/", methods=["GET"])
def search_sessions():
    token_error = validate_secret_token()
    if token_error:
        return token_error
    try:
        if not request.args:
            raise BadRequest("request arguments are required.")

        return search_sessions_use_case(request.args)

    except ValueError as e:
        return jsonify({"error": str(e)}), 422

    except BadRequest as e:
        return jsonify({"error": str(e)}), 400

    except Exception as e:
        return jsonify({"error": f"Internal server error {str(e)}"}), 500


@session_bp.route("/approve", methods=["POST"])
def approve_session():
    token_error = validate_secret_token()
    if token_error:
        return token_error
    try:
        external_id = request.args.get("externalSesionId")
        body = request.get_json()
        if not body or not external_id:
            raise BadRequest("missing required parameters or body")
        result = approve_session_use_case(body, external_id)
        return jsonify(result), 200
    except LookupError as e:
        return jsonify({"error": str(e)}), 404

    except ValueError as e:
        return jsonify({"error": str(e)}), 422

    except BadRequest as e:
        return jsonify({"error": str(e)}), 400

    except Exception as e:
        return jsonify({"error": f"Internal server error {str(e)}"}), 500
