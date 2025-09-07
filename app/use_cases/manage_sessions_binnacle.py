from flask import jsonify
from app.repositories.session_binnacle_repository import (
    create_session_binnacle,
    list_all_session_binnacles,
    get_session_binnacle_by_id,
    get_binnacles_by_session_id,
    get_binnacles_by_external_session_id,
    get_binnacles_by_project_name,
    get_binnacles_by_start_date,
    get_binnacles_by_user_email,
    get_binnacles_by_start_date_range
)
from app.use_cases.manage_error_log import log_error_use_case
from app.validators.date_validator import parse_date_param
from app.validators.session_binnacle_validator import validate_session_binnacle_data

def search_session_binnacles_use_case(params):
    try:

        email = params.get("email")
        external_id = params.get("external_sesion_id")
        project = params.get("projectName")

        #validar y convertir fechas
        start_date_raw = params.get("startDate")
        from_date_raw = params.get("fromDate")
        to_date_raw = params.get("toDate")

        start_date, error = parse_date_param(start_date_raw, "startDate")
        if error:
            raise ValueError(error)

        from_date, error = parse_date_param(from_date_raw, "fromDate")
        if error:
            raise ValueError(error)

        to_date, error = parse_date_param(to_date_raw, "toDate")
        if error:
            raise ValueError(error)

        results = []

        if email:
            results.extend(get_binnacles_by_user_email(email))
        if external_id:
            results.extend(get_binnacles_by_external_session_id(external_id))
        if project:
            results.extend(get_binnacles_by_project_name(project))
        if start_date:
            results.extend(get_binnacles_by_start_date(start_date))
        if from_date:
            results.extend(get_binnacles_by_start_date_range(from_date, to_date))

        if not any([email, external_id, project, start_date, from_date]):
            results = list_all_session_binnacles()

        unique_results = {b.idSesionBinnacle: b for b in results}.values()
        return jsonify([serialize_session_binnacle(b) for b in unique_results]), 200
    except ValueError as e:
        log_error_use_case(
            endpoint="/api-clockify/session-binnacle/search",
            method="GET",
            error=e,
            payload=params,
            response_code=422
        )
        raise
    except Exception as e:
        log_error_use_case(
            endpoint="/api-clockify/session-binnacle/search",
            method="GET",
            error=e,
            payload=params,
            response_code=500
        )
        raise e

def serialize_session_binnacle(b):
    return {
        "idSesionBinnacle": b.idSesionBinnacle,
        "external_sesion_id": b.external_sesion_id,
        "idSesion": b.idSesion,
        "description": b.description,
        "idUser": b.idUser,
        "idProject": b.idProject,
        "projectName": b.projectName,
        "idWorkspace": b.idWorkspace,
        "workspaceName": b.workspaceName,
        "idTask": b.idTask,
        "taskName": b.taskName,
        "startDate": b.startDate.isoformat() if b.startDate else None,
        "endDate": b.endDate.isoformat() if b.endDate else None,
        "createdAt": b.createdAt.isoformat() if b.createdAt else None,
        "modifiedAt": b.modifiedAt.isoformat() if b.modifiedAt else None,
        "duration": str(b.duration) if b.duration is not None else None,
        "timeZone": b.timeZone,
        "offsetStart": b.offsetStart,
        "offsetEnd": b.offsetEnd,
        "updatingQuantity": b.updatingQuantity,
        "enable": b.enable,
        "disableTime": b.disableTime.isoformat() if b.disableTime else None
    }


def list_session_binnacles_use_case():
    try:
        binnacles = list_all_session_binnacles()
        return jsonify([serialize_session_binnacle(b) for b in binnacles]), 200
    except Exception as e:
        log_error_use_case(
            endpoint="/api-clockify/session-binnacle/getAll",
            method="GET",
            error=e,
            payload={"data": None},
            response_code=500
        )
        raise e


def get_session_binnacle_use_case(id_binnacle):
    try:
        b = get_session_binnacle_by_id(id_binnacle)
        if not b:
            raise LookupError("error Binnacle entry not found")
        return jsonify(serialize_session_binnacle(b)), 200
    except LookupError as e:
        log_error_use_case(
            endpoint="/api-clockify/session-binnacle/getByIdSession",
            method="GET",
            error=e,
            payload={"data": None},
            response_code=404
        )
        raise e
    except Exception as e:
        log_error_use_case(
            endpoint="/api-clockify/session-binnacle/getById",
            method="GET",
            error=e,
            payload={"data": None},
            response_code=500
        )
        raise e


def get_session_binnacles_by_session_use_case(id_sesion):
    try:
        if not id_sesion:
            raise ValueError("id session cannot be None")
        binnacles = get_binnacles_by_session_id(id_sesion)
        return jsonify([serialize_session_binnacle(b) for b in binnacles]), 200
    except ValueError as e:
        log_error_use_case(
            endpoint="/api-clockify/session-binnacle/getByIdSession",
            method="GET",
            error=e,
            payload=id_sesion,
            response_code=422
        )
        raise
    except Exception as e:
        log_error_use_case(
            endpoint="/api-clockify/session-binnacle/getByIdSession",
            method="GET",
            error=e,
            payload=id_sesion,
            response_code=422
        )
        raise e


def create_session_binnacle_use_case(data):
    try:
        is_valid, errors = validate_session_binnacle_data(data)
        if not is_valid:
            return jsonify({"error": "Validation failed", "details": errors}), 400

        b = create_session_binnacle(data)
        return jsonify({
            "message": "Binnacle entry created",
            "id": b.idSesionBinnacle
        }), 201
    except ValueError as e:
        log_error_use_case(
            endpoint="/api-clockify/session-binnacle/create",
            method="POST",
            error=e,
            payload=data,
            response_code=422
        )
        raise
    except Exception as e:
        log_error_use_case(
            endpoint="/api-clockify/session-binnacle/create",
            method="POST",
            error=e,
            payload=data,
            response_code=500
        )
        raise e