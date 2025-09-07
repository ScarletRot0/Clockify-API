from app.extensions import db
from app.models.email_queue import EmailQueue
from app.mappers.email_queue_mapper import map_email_to_queue_entity
from app.validators.email_queue_validator import validate_email_queue_data
from app.use_cases.manage_error_log import log_error_use_case
from sqlalchemy.exc import SQLAlchemyError


def enqueue_email(subject, data, to_address, attachments=None):
    try:
        # Mapear y validar
        data = map_email_to_queue_entity(to_address, subject, data, attachments)
        is_valid, errors = validate_email_queue_data(data)

        if not is_valid:
            raise ValueError(f"Invalid email queue data: {errors}")

        # Crear y guardar en base de datos
        email = EmailQueue(**data)
        db.session.add(email)
        db.session.commit()

    except ValueError as ve:
        # Error de validación explícito
        log_error_use_case(
            endpoint="enqueue_email",
            method="SYSTEM",
            error=ve,
            payload={"to": to_address, "subject": subject, "body": data},
            response_code=422
        )
        raise ve

    except SQLAlchemyError as db_err:
        # Error al interactuar con la base de datos
        db.session.rollback()
        log_error_use_case(
            endpoint="enqueue_email",
            method="SYSTEM",
            error=db_err,
            payload={"to": to_address, "subject": subject, "body": data},
            response_code=500
        )
        raise RuntimeError("Database error while enqueuing email") from db_err

    except Exception as e:
        # Otro error inesperado
        db.session.rollback()
        log_error_use_case(
            endpoint="enqueue_email",
            method="SYSTEM",
            error=e,
            payload={"to": to_address, "subject": subject, "body": data},
            response_code=500
        )
        raise RuntimeError("Unexpected error while enqueuing email") from e
