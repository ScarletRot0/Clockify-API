from app.models.session import Session
from app.models.session_binnacle import SessionBinnacle
from app.extensions import db
from app.validators.approve_validator import validate_approve_session_data
from app.mappers.webhook_mapper import map_session_to_binnacle_data
from app.use_cases.manage_error_log import log_error_use_case

def approve_session_use_case(data, external_id):
    try:
        # Validar el body
        is_valid, errors = validate_approve_session_data(data)
        if not is_valid:
            raise ValueError(f"Invalid Payload: {errors}")

        aprobado = data["aprobado"]
        observacion = data["observacion"]

        # Buscar sesión por external_id
        session = Session.query.filter_by(external_sesion_id=external_id).first()
        if not session:
            raise LookupError(f"No se encontró la sesión con external_sesion_id: {external_id}")

        # Verificar si la sesión está en estado editable
        if session.status != "EN OBSERVACION":
            raise ValueError(f"La sesión no está en estado EN OBSERVACION. Estado actual: {session.status}")

        # Actualizar estado y observacion
        session.status = "APROBADO" if aprobado else "REPROBADO"
        session.observation = observacion

        if aprobado:
            session.ValidStartDate = session.startDate
            session.ValidEndDate = session.endDate
            session.ValidDuration = session.duration

        #registrar en binnacle
        db.session.add(SessionBinnacle(**map_session_to_binnacle_data(session)))
        db.session.commit()

        return {"message": f"Sesión {'aprobada' if aprobado else 'reprobada'} correctamente"}

    except ValueError as e:
        db.session.rollback()
        log_error_use_case(
            endpoint="/api-clockify/sessions/approve",
            method="POST",
            error=e,
            payload=data,
            response_code=422
        )
        raise
    except LookupError as e:
        db.session.rollback()
        log_error_use_case(
            endpoint="/api-clockify/sessions/approve",
            method="POST",
            error=e,
            payload=data,
            response_code=404
        )
        raise
    except Exception as e:
        db.session.rollback()
        log_error_use_case(
            endpoint="/api-clockify/sessions/approve",
            method="POST",
            error=e,
            payload=data,
            response_code=500
        )
        raise