from flask import jsonify
from app.repositories.session_repository import (
    list_sessions,
    get_session_by_id,
    get_sessions_by_user_id,
    get_sessions_by_user_email,
    create_session,
    update_session,
    delete_session,get_sessions_by_start_date,
    get_sessions_by_start_date_range
)
from app.use_cases.manage_error_log import log_error_use_case
from app.validators.date_validator import parse_date_param
from app.validators.session_validator import validate_session_data

def search_sessions_use_case(params):
    try:
        from_date_raw = params.get("fromDate")
        to_date_raw = params.get("toDate")
        date_raw = params.get("startDate")

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
            results.extend(get_sessions_by_start_date(start_date))
        if from_date:
            results.extend(get_sessions_by_start_date_range(from_date, to_date))

        if not results:
            results = list_sessions()

        unique = {s.idSesion: s for s in results}.values()
        return jsonify([serialize_session(s) for s in unique]), 200
    except ValueError as e:
        log_error_use_case(
            endpoint="/api-clockify/sessions/search",
            method="GET",
            error=e,
            payload=params,
            response_code=422
        )
        raise
    except Exception as e:
        log_error_use_case(
            endpoint="/api-clockify/sessions/search",
            method="GET",
            error=e,
            payload=params,
            response_code=500
        )
        raise e

def serialize_session(s):
    return {
        "idSesion": s.idSesion,
        "external_sesion_id": s.external_sesion_id,
        "description": s.description,
        "idUser": s.idUser,
        "idProject": s.idProject,
        "projectName": s.projectName,
        "idWorkspace": s.idWorkspace,
        "workspaceName": s.workspaceName,
        "idTask": s.idTask,
        "taskName": s.taskName,
        "startDate": s.startDate.isoformat() if s.startDate else None,
        "endDate": s.endDate.isoformat() if s.endDate else None,
        "duration": str(s.duration) if s.duration is not None else None,
        "timeZone": s.timeZone,
        "offsetStart": s.offsetStart,
        "offsetEnd": s.offsetEnd,
        "currentlyRunning": s.currentlyRunning,
        "overtime": s.overtime,
        "enable": s.enable,
        "disableTime": s.disableTime.isoformat() if s.disableTime else None,
        "updatingQuantity": s.updatingQuantity
    }


def list_sessions_use_case():
    try:
        sessions = list_sessions()
        return [serialize_session(s) for s in sessions]
    except Exception as e:
        log_error_use_case(
            endpoint="/api-clockify/sessions/getAll",
            method="GET",
            error=e,
            payload={"data": None},
            response_code=500
        )
        raise e


def get_session_by_id_use_case(session_id):
    try:
        s = get_session_by_id(session_id)
        if not s:
            raise LookupError("error: Session not found")

        return jsonify(serialize_session(s)), 200
    except LookupError as e:
        log_error_use_case(
            endpoint="/api-clockify/sessions/getById/",
            method="GET",
            error=e,
            payload=session_id,
            response_code=404
        )
        raise
    except Exception as e:
        log_error_use_case(
            endpoint="/api-clockify/sessions/getById/",
            method="GET",
            error=e,
            payload=session_id,
            response_code=500
        )
        raise e

def get_session_by_id_user_use_case(user_id):
    try:
        sessions = get_sessions_by_user_id(user_id)
        return jsonify([serialize_session(s) for s in sessions]), 200
    except LookupError as e:
        log_error_use_case(
            endpoint="/api-clockify/sessions/getByUser/",
            method="GET",
            error=e,
            payload=user_id,
            response_code=404
        )
        raise
    except Exception as e:
        log_error_use_case(
            endpoint="/api-clockify/sessions/getByUser/",
            method="GET",
            error=e,
            payload=user_id,
            response_code=500
        )
        raise e


def get_session_by_email_user_use_case(email):
    try:
        sessions = get_sessions_by_user_email(email)
        return jsonify([serialize_session(s) for s in sessions]), 200
    except LookupError as e:
        log_error_use_case(
            endpoint="/api-clockify/sessions/getByEmail/",
            method="GET",
            error=e,
            payload=email,
            response_code=404
        )
        raise
    except Exception as e:
        log_error_use_case(
            endpoint="/api-clockify/sessions/getByEmail/",
            method="GET",
            error=e,
            payload=email,
            response_code=500
        )
        raise e


def create_session_use_case(data):
    try:
        is_valid, errors = validate_session_data(data)
        if not is_valid:
            raise ValueError(f"Validation failed, details: {errors}")

        session = create_session(data)
        return jsonify({"message": "Session created", "id": session.idSesion}), 201
    except ValueError as e:
        log_error_use_case(
            endpoint="/api-clockify/sessions/create",
            method="POST",
            error=e,
            payload=data,
            response_code=404
        )
        raise
    except Exception as e:
        log_error_use_case(
            endpoint="/api-clockify/sessions/create",
            method="POST",
            error=e,
            payload=data,
            response_code=500
        )
        raise e


def update_session_use_case(session_id, data):
    try:
        is_valid, errors = validate_session_data(data, is_update=True)
        if not is_valid:
            return jsonify({"error": "Validation failed", "details": errors}), 400

        session = update_session(session_id, data)
        if not session:
            return jsonify({"error": "Session not found"}), 404

        return jsonify({"message": "Session updated"}), 200
    except ValueError as ve:
        log_error_use_case(
            endpoint="/api-clockify/sessions/update",
            method="PUT",
            error=ve,
            payload=data,
            response_code=422
        )
        raise

    except LookupError as le:
        log_error_use_case(
            endpoint="/api-clockify/sessions/update",
            method="PUT",
            error=le,
            payload={"session_id": session_id},
            response_code=404
        )
        raise

    except Exception as e:
        log_error_use_case(
            endpoint="/api-clockify/sessions/update",
            method="PUT",
            error=e,
            payload=data,
            response_code=500
        )
        raise e


def delete_session_use_case(session_id):
    try:
        success = delete_session(session_id)
        if not success:
            return jsonify({"error": "Session not found"}), 404

        return jsonify({"message": "Session deleted"}), 200
    except LookupError as le:
        log_error_use_case(
            endpoint="/api-clockify/sessions/delete",
            method="PUT",
            error=le,
            payload={"session_id": session_id},
            response_code=404
        )
        raise

