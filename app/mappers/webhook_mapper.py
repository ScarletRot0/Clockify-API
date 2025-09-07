from datetime import datetime, UTC
from dateutil import parser
from app.use_cases.manage_error_log import log_error_use_case
import isodate

def map_webhook_user_to_user_entity(webhook_data):
    user_data = webhook_data.get("user", {})
    status = user_data.get("status", "").upper()
    is_enabled = status == "ACTIVE"

    return {
        "ExternalUserId": user_data.get("id"),
        "name": user_data.get("name"),
        "email": f"{user_data.get('id')}@clockify.fake",  # Evitar email vacío y mantener unicidad
        "hoursPerMonth": 0,
        "enable": is_enabled,
        "disabledTime": None if is_enabled else datetime.now(UTC)
    }

def map_webhook_to_session_entity(data):
    time_data = data.get("timeInterval", {})
    project = data.get("project") or {}
    task = data.get("task") or {}
    user = data.get("user") or {}

    is_enabled = True  # Forzado como activo por defecto

    # Inicialización segura
    start_raw = time_data.get("start")
    end_raw = time_data.get("end")
    duration_raw = time_data.get("duration")

    start_parsed, end_parsed, duration_parsed = None, None, None

    try:
        if start_raw:
            start_parsed = parser.isoparse(start_raw)
    except Exception as e:
        log_error_use_case(
            endpoint="map_webhook_to_session_entity",
            method="SYSTEM",
            error=f"Error parseando startDate: {str(e)}",
            payload={"start_raw": start_raw, "full_data": data},
            response_code=422
        )

    try:
        if end_raw:
            end_parsed = parser.isoparse(end_raw)
    except Exception as e:
        log_error_use_case(
            endpoint="map_webhook_to_session_entity",
            method="SYSTEM",
            error=f"Error parseando endDate: {str(e)}",
            payload={"end_raw": end_raw, "full_data": data},
            response_code=422
        )

    try:
        if duration_raw:
            duration_parsed = isodate.parse_duration(duration_raw)
    except Exception as e:
        log_error_use_case(
            endpoint="map_webhook_to_session_entity",
            method="SYSTEM",
            error=f"Error parseando duration: {str(e)}",
            payload={"duration_raw": duration_raw, "full_data": data},
            response_code=422
        )

    # Alerta si es cierre o edición y no vino endDate
    if not data.get("currentlyRunning", True) and not end_parsed:
        log_error_use_case(
            endpoint="map_webhook_to_session_entity",
            method="SYSTEM",
            error="Webhook con cierre/edición recibido sin endDate válido",
            payload=data,
            response_code=206  # Partial Content
        )

    session_dict = {
        "external_sesion_id": data.get("id"),
        "description": data.get("description") or "Sin descripción",
        "idUser": user.get("id"),
        "idProject": data.get("projectId", "") or "",
        "projectName": project.get("name", "Sin proyecto"),
        "idWorkspace": data.get("workspaceId", ""),
        "workspaceName": "ActionTracker",
        "idTask": task.get("id", "") or "",
        "taskName": task.get("name", "Sin tarea"),
        "startDate": start_parsed,
        "endDate": end_parsed,
        "duration": duration_parsed,
        "timeZone": time_data.get("timeZone", ""),
        "offsetStart": time_data.get("offsetStart", 0),
        "offsetEnd": time_data.get("offsetEnd", 0),
        "currentlyRunning": data.get("currentlyRunning", False),
        "enable": is_enabled,
        "disableTime": None if is_enabled else datetime.now(UTC),
    }

    return session_dict

def map_session_to_binnacle_data(session):
    return {
        "external_sesion_id": session.external_sesion_id,
        "idSesion": session.idSesion,
        "description": session.description,
        "idUser": session.idUser,
        "idProject": session.idProject,
        "projectName": session.projectName,
        "idWorkspace": session.idWorkspace,
        "workspaceName": session.workspaceName,
        "idTask": session.idTask,
        "taskName": session.taskName,
        "startDate": session.startDate,
        "endDate": session.endDate,
        "createdAt": datetime.now(UTC),
        "modifiedAt": datetime.now(UTC),
        "duration": session.duration,
        "timeZone": session.timeZone,
        "offsetStart": session.offsetStart,
        "offsetEnd": session.offsetEnd,
        "updatingQuantity": session.updatingQuantity,
        "enable": session.enable,
        "disableTime": session.disableTime,
        # Nuevos campos
        "ValidStartDate": session.ValidStartDate,
        "ValidEndDate": session.ValidEndDate,
        "ValidDuration": session.ValidDuration,
        "status": session.status,
        "observation": session.observation,
    }