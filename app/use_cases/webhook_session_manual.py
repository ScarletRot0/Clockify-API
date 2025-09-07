from datetime import datetime

from app.models.session import Session
from app.models.session_binnacle import SessionBinnacle
from app.models.user import User
from app.extensions import db
from app.mappers.webhook_mapper import (
    map_webhook_user_to_user_entity,
    map_webhook_to_session_entity,
    map_session_to_binnacle_data
)
from flask import jsonify
from app.use_cases.manage_error_log import log_error_use_case
from app.services.email_queue_service import enqueue_email
from app.validators.webhook_validator import validate_webhook_data
from pytz import timezone, UnknownTimeZoneError


def handle_session_manual_creation_use_case(data):
    try:
        # Validar payload
        print("Duplicacion activada")
        is_valid, errors = validate_webhook_data(data)
        if not is_valid:
            raise ValueError(f"Invalid payload: {errors}")

        # Procesar usuario
        user_info = map_webhook_user_to_user_entity(data)
        external_user_id = user_info["ExternalUserId"]

        existing_user = User.query.filter_by(external_user_id=external_user_id).first()
        if existing_user:
            existing_user.name = user_info["name"]
            existing_user.enable = user_info["enable"]
            existing_user.disabled_time = user_info["disabledTime"]
        else:
            new_user = User(
                external_user_id=external_user_id,
                name=user_info["name"],
                email=user_info["email"],
                hours_per_month=user_info["hoursPerMonth"],
                enable=user_info["enable"],
                disabled_time=user_info["disabledTime"]
            )
            db.session.add(new_user)
            db.session.flush()
            existing_user = new_user

        #verificar si ya existe la sesion
        external_id = data.get("id")
        existing_session = Session.query.filter_by(external_sesion_id=external_id).first()
        if existing_session:
            raise ValueError(f"Duplicated session ID: session with external ID {external_id} already exists")

        #crear nueva sesion
        session_data = map_webhook_to_session_entity(data)
        session_data["idUser"] = existing_user.id
        new_session = Session(**session_data)
        if new_session.startDate is None and session_data.get("startDate"):
            new_session.startDate = session_data["startDate"]
        if new_session.endDate is None and session_data.get("endDate"):
            new_session.endDate = session_data["endDate"]
        db.session.add(new_session)
        db.session.flush()
        # Verificar si es overtime
        if new_session.duration and new_session.duration.total_seconds() > 5 * 3600:
            new_session.overtime = True

        #guardar en binnacle
        binnacle_data = map_session_to_binnacle_data(new_session)
        db.session.add(SessionBinnacle(**binnacle_data))
        db.session.commit()
        if existing_user.indNotificar:
            try:
                tz = timezone(new_session.timeZone)
            except UnknownTimeZoneError:
                tz = timezone("UTC")

            local_start = new_session.startDate.astimezone(tz)
            local_end = new_session.endDate.astimezone(tz) if new_session.endDate else None
            # Enviar correo de alerta de sesion manual
            body = f"""
    <html>
    <body style="font-family: Arial, sans-serif; color: #333;">
      <div style="background-color: #fffde7; padding: 10px; font-size: 20px; font-weight: bold; color: #f9a825; border-left: 6px solid #fbc02d;">
        ⚠️ SESIÓN CREADA MANUALMENTE
      </div>
    
      <p><strong style="color: #f57f17;">👤 Usuario:</strong> {existing_user.name} ({existing_user.email})</p>
      <p><strong style="color: #f57f17;">🔗 Sesión ID externa:</strong> {external_id}</p>
      <p><strong style="color: #f57f17;">📝 Descripción:</strong> {new_session.description or 'Sin descripción'}</p>
      <p><strong style="color: #f57f17;">📁 Proyecto:</strong> {new_session.projectName or 'Sin proyecto'}</p>
      <p><strong style="color: #f57f17;">📌 Tarea:</strong> {new_session.taskName or 'Sin tarea'}</p>
    
      <hr style="border:1px dotted black" />
    
      <p><strong style="color: #f57f17;">📆 Inicio (reloj Usuario):</strong> <code>{local_start.strftime('%Y-%m-%d %H:%M:%S %Z')}</code></p>
      <p><strong style="color: #1b5e20;">📆 Inicio (UTC registrado):</strong> <code>{new_session.startDate}</code></p>
      <p><strong style="color: #f57f17;">📆 Fin (reloj Usuario):</strong> <code>{local_end.strftime('%Y-%m-%d %H:%M:%S %Z') if local_end else 'N/A'}</code></p>
      <p><strong style="color: #1b5e20;">📆 Fin (UTC registrado):</strong> <code>{new_session.endDate}</code></p>
      <p><strong style="color: #f57f17;">⏱️ Duración:</strong> {new_session.duration}</p>
      <p><strong style="color: #f57f17;">⏰ Overtime:</strong> {'Sí' if new_session.overtime else 'No'}</p>
    
      <div style="background-color: #ffebee; padding: 10px; border-left: 6px solid #c62828; color: #b71c1c; margin-top: 20px;">
        ⚠️ La creación manual de sesiones <strong>no está permitida</strong>. 
        Esta sesión <strong>no se contará para el TTS</strong> salvo que sea revisada y aprobada. <br/>
        Si necesitas registrar una jornada, contacta a tu coordinador responsable.
      </div>
    </body>
    </html>
    """
            enqueue_email(
                subject=f"Clockify - ALERTA: Sesion creada manualmente en Clockify - {existing_user.name} - ({datetime.now(tz).strftime('%Y-%m-%d %H:%M')})",
                data=body, to_address=existing_user.email
            )

        return {"message": "Manual session created and logged in binnacle"}
    except ValueError as e:
        db.session.rollback()
        log_error_use_case(
            endpoint="/api-clockify/webhook/manual",
            method="POST",
            error=e,
            payload=data,
            response_code=422
        )
        raise
    except Exception as e:
        db.session.rollback()
        log_error_use_case(
            endpoint="/api-clockify/webhook/manual",
            method="POST",
            error=e,
            payload=data,
            response_code=500
        )
        raise e