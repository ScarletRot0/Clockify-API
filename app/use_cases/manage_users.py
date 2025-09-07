from app.repositories.user_repository import (
    get_all_users,
    get_user_by_email,
    get_user_by_external_id,
    create_user,
    update_user_by_external_id,
    delete_user_by_external_id,get_users_with_session_on,
    get_users_with_session_between
)
from app.validators.date_validator import parse_date_param
from flask import jsonify
from app.use_cases.manage_error_log import log_error_use_case
from app.validators.user_validator import validate_user_data

def search_users_use_case(params):
    try:
        date_raw = params.get("startDate")
        from_date_raw = params.get("fromDate")
        to_date_raw = params.get("toDate")

        start_date, error = parse_date_param(date_raw, "startDate")
        if error:
            raise ValueError(f"error: Invalid date format for 'startDate'")

        from_date, error = parse_date_param(from_date_raw, "fromDate")
        if error:
            raise ValueError(f"error: Invalid date format for 'fromDate'")

        to_date, error = parse_date_param(to_date_raw, "toDate")
        if error:
            raise ValueError(f"error: Invalid date format for 'toDate'")

        results = []

        if start_date:
            results.extend(get_users_with_session_on(start_date))
        if from_date:
            results.extend(get_users_with_session_between(from_date, to_date))

        if not any([start_date, from_date]):
            results = get_all_users()

        unique_users = {u.id: u for u in results}.values()

        return jsonify([
            {
                'id': u.id,
                'ExternalUserId': u.external_user_id,
                'name': u.name,
                'email': u.email,
                'hoursPerMonth': u.hours_per_month,
                'enable': u.enable,
                'disabledTime': u.disabled_time.isoformat() if u.disabled_time else None,
                'notify': u.indNotificar
            }
            for u in unique_users
        ]), 200
    except ValueError as e:
        log_error_use_case(
            endpoint="/api-clockify/users/search",
            method="GET",
            error=e,
            payload=params,
            response_code=422
        )
        raise
    except Exception as e:
        log_error_use_case(
            endpoint="/api-clockify/users/search",
            method="GET",
            error=e,
            payload=params,
            response_code=500
        )
        raise e


def list_users_use_case():
    try:
        users = get_all_users()
        return [
            {
                'id': u.id,
                'ExternalUserId': u.external_user_id,
                'name': u.name,
                'email': u.email,
                'hoursPerMonth': u.hours_per_month,
                'enable': u.enable,
                'disabledTime': u.disabled_time.isoformat() if u.disabled_time else None,
                'notify': u.indNotificar
            }
            for u in users
        ]
    except Exception as e:
        log_error_use_case(
            endpoint="/api-clockify/users/getAll",
            method="GET",
            error=e,
            payload={"data": None},
            response_code=500
        )
        raise e



def get_user_by_external_id_use_case(external_id):
    try:
        u = get_user_by_external_id(external_id)
        if not u:
            raise LookupError("error: User not found")

        return jsonify({
            'id': u.id,
            'ExternalUserId': u.external_user_id,
            'name': u.name,
            'email': u.email,
            'hoursPerMonth': u.hours_per_month,
            'enable': u.enable,
            'disabledTime': u.disabled_time.isoformat() if u.disabled_time else None,
            'notify': u.indNotificar
        }), 200
    except LookupError as e:
        log_error_use_case(
            endpoint="/api-clockify/users/getByExternalId/",
            method="GET",
            error=e,
            payload=external_id,
            response_code=404
        )
        raise
    except Exception as e:
        log_error_use_case(
            endpoint="/api-clockify/users/getByExternalId/",
            method="GET",
            error=e,
            payload=external_id,
            response_code=500
        )
        raise e


def get_user_by_email_use_case(email):
    try:
        u = get_user_by_email(email)
        if not u:
            raise LookupError("User not found")

        return jsonify({
            'id': u.id,
            'ExternalUserId': u.external_user_id,
            'name': u.name,
            'email': u.email,
            'hoursPerMonth': u.hours_per_month,
            'enable': u.enable,
            'disabledTime': u.disabled_time.isoformat() if u.disabled_time else None,
            'notify': u.indNotificar
        }), 200
    except ValueError as e:
        log_error_use_case(
            endpoint="/api-clockify/users/getByEmail",
            method="GET",
            error=e,
            payload=email,
            response_code=404
        )
        raise
    except Exception as e:
        log_error_use_case(
            endpoint="/api-clockify/users/getByEmail",
            method="GET",
            error=e,
            payload=email,
            response_code=500
        )
        raise e


def create_user_use_case(data):
    try:
        is_valid, errors = validate_user_data(data)
        if not is_valid:
            raise ValueError(f"Validation failed, details: {errors}")

        user = create_user(data)
        return jsonify({
            'id': user.id,
            'ExternalUserId': user.external_user_id,
            'name': user.name,
            'email': user.email,
            'hoursPerMonth': user.hours_per_month,
            'enable': user.enable,
            'disabledTime': user.disabled_time.isoformat() if user.disabled_time else None,
            'notify': user.indNotificar
        }), 201
    except ValueError as e:
        log_error_use_case(
            endpoint="/api-clockify/users/create",
            method="POST",
            error=e,
            payload=data,
            response_code=422
        )
        raise
    except Exception as e:
        log_error_use_case(
            endpoint="/api-clockify/users/create",
            method="POST",
            error=e,
            payload=data,
            response_code=500
        )
        raise e

def update_user_by_external_id_use_case(external_id, data):
    try:
        is_valid, errors = validate_user_data(data, is_update=True)
        if not is_valid:
            raise ValueError(f"Validation failed: {errors}")

        user = update_user_by_external_id(external_id, data)
        if not user:
            raise LookupError("User not found")

        return jsonify({
            'id': user.id,
            'ExternalUserId': user.external_user_id,
            'name': user.name,
            'email': user.email,
            'hoursPerMonth': user.hours_per_month,
            'enable': user.enable,
            'disabledTime': user.disabled_time.isoformat() if user.disabled_time else None,
            'notify': user.indNotificar
        }), 200

    except ValueError as ve:
        log_error_use_case(
            endpoint="/api-clockify/users/update",
            method="PUT",
            error=ve,
            payload=data,
            response_code=422
        )
        raise

    except LookupError as le:
        log_error_use_case(
            endpoint="/api-clockify/users/update",
            method="PUT",
            error=le,
            payload={"external_id": external_id},
            response_code=404
        )
        raise

    except Exception as e:
        log_error_use_case(
            endpoint="/api-clockify/users/update",
            method="PUT",
            error=e,
            payload=data,
            response_code=500
        )
        raise e

def delete_user_by_external_id_use_case(external_id):
    try:
        success = delete_user_by_external_id(external_id)
        if not success:
            raise LookupError("User not found")

        return jsonify({"message": "User deleted"}), 200
    except LookupError as le:
        log_error_use_case(
            endpoint="/api-clockify/users/delete",
            method="PUT",
            error=le,
            payload={"external_id": external_id},
            response_code=404
        )
        raise
