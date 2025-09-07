from flask import Blueprint, request, jsonify
from werkzeug.exceptions import BadRequest

from app.use_cases.manage_users import (
    list_users_use_case,
    get_user_by_external_id_use_case,
    get_user_by_email_use_case,
    create_user_use_case,
    update_user_by_external_id_use_case,
    delete_user_by_external_id_use_case,
    search_users_use_case
)
from app.use_cases.validate_token import validate_secret_token
user_bp = Blueprint('users', __name__, url_prefix='/api-clockify/users')

@user_bp.route('/getAll/', methods=['GET'])
def index():
    token_error = validate_secret_token()
    if token_error:
        return token_error
    try:
        return list_users_use_case()
    except Exception as e:
        return jsonify({"error": f"Internal server error {e}"}), 500
@user_bp.route('/getByExternalId/<string:external_id>', methods=['GET'])
def show_by_external_id(external_id):
    token_error = validate_secret_token()
    if token_error:
        return token_error
    try:
        if not external_id:
            raise BadRequest("external id is required.")

        return get_user_by_external_id_use_case(external_id)

    except LookupError as e:
        return jsonify({"error": str(e)}), 404

    except BadRequest as e:
        return jsonify({"error": str(e)}), 400

    except Exception as e:
        return jsonify({"error": f"Internal server error {e}"}), 500

@user_bp.route('/getByEmail/<string:email>', methods=['GET'])
def show_by_email(email):
    token_error = validate_secret_token()
    if token_error:
        return token_error
    try:
        if not email:
            raise BadRequest("email is required.")

        return get_user_by_email_use_case(email)

    except LookupError as e:
        return jsonify({"error": str(e)}), 404

    except BadRequest as e:
        return jsonify({"error": str(e)}), 400

    except Exception as e:
        return jsonify({"error": f"Internal server error {e}"}), 500

@user_bp.route('/create/', methods=['POST'])
def create():
    token_error = validate_secret_token()
    if token_error:
        return token_error
    try:
        data = request.get_json()
        if not data:
            raise BadRequest("JSON body is required.")

        return create_user_use_case(data)

    except ValueError as e:
        return jsonify({"error": str(e)}), 422

    except BadRequest as e:
        return jsonify({"error": str(e)}), 400

    except Exception as e:
        return jsonify({"error": f"Internal server error {e}"}), 500

@user_bp.route('/update/<string:external_id>', methods=['PUT'])
def update_by_external_id(external_id):
    token_error = validate_secret_token()
    if token_error:
        return token_error
    try:
        data = request.get_json()
        if not data or not external_id:
            raise BadRequest("JSON body or external id is required.")

        return update_user_by_external_id_use_case(external_id, data)

    except ValueError as e:
        return jsonify({"error": str(e)}), 422

    except LookupError as e:
        return jsonify({"error": str(e)}), 404

    except BadRequest as e:
        return jsonify({"error": str(e)}), 400

    except Exception as e:
        return jsonify({"error": f"Internal server error {e}"}), 500

@user_bp.route('/deleteByExternalId/<string:external_id>', methods=['DELETE'])
def delete_by_external_id(external_id):
    token_error = validate_secret_token()
    if token_error:
        return token_error
    try:
        if not external_id:
            raise BadRequest("external id is required.")

        return delete_user_by_external_id_use_case(external_id)

    except LookupError as e:
        return jsonify({"error": str(e)}), 404

    except BadRequest as e:
        return jsonify({"error": str(e)}), 400

    except Exception as e:
        return jsonify({"error": f"Internal server error {e}"}), 500

@user_bp.route("/search/", methods=["GET"])
def search_users():
    token_error = validate_secret_token()
    if token_error:
        return token_error
    try:
        if not request.args:
            raise BadRequest("request arguments are required.")

        return search_users_use_case(request.args)

    except ValueError as e:
        return jsonify({"error": str(e)}), 422

    except BadRequest as e:
        return jsonify({"error": str(e)}), 400

    except Exception as e:
        return jsonify({"error": f"Internal server error {e}"}), 500