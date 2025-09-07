from flask import Blueprint, request, jsonify
from werkzeug.exceptions import BadRequest
from app.use_cases.send_periodic_reports import send_periodic_report
from app.use_cases.validate_token import validate_secret_token
from app.use_cases.send_manual_report import send_user_report_use_case
report_bp = Blueprint("report", __name__, url_prefix="/api-clockify/session-report")

@report_bp.route("/sendAllReports", methods=["POST"])
def test_report():
    try:
        token_error = validate_secret_token()
        if token_error:
            return token_error

        data = request.get_json() or {}

        report_type = data.get("type", "weekly")
        month = data.get("month")
        year = data.get("year")
        start_date = data.get("start_date")
        if not report_type:
            raise BadRequest("missing required parameters")
        send_periodic_report(report_type, month=month, year=year, start_date=start_date)
        return jsonify({"message": f"{report_type} report sent (test mode)"}), 200
    except BadRequest as e:
        return jsonify({"error": str(e)}), 400
    except ValueError as e:
        return jsonify({"error": str(e)}), 422
    except Exception as e:
        return jsonify({"error: Internal server error": str(e)}), 500

@report_bp.route("/user", methods=["POST"])
def send_user_report():
    token_error = validate_secret_token()
    if token_error:
        return token_error
    try:
        data = request.get_json()
        id_user = data.get("idUser")
        start_date_str = data.get("startDate")
        end_date_str = data.get("endDate")
        email_to_send = data.get("emailToSend")
        if not id_user or not start_date_str or not end_date_str or not email_to_send:
            raise BadRequest("missing required parameters")
        result = send_user_report_use_case(id_user, start_date_str, end_date_str, email_to_send)
        return jsonify(result), 200
    except LookupError as e:
        return jsonify({"error": str(e)}), 404

    except ValueError as e:
        return jsonify({"error": str(e)}), 422

    except BadRequest as e:
        return jsonify({"error": str(e)}), 400

    except Exception as e:
        return jsonify({"error": f"Internal server error {str(e)}"}), 500