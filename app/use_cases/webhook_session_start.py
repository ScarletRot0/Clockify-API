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
from app.validators.webhook_validator import validate_webhook_data
from pytz import timezone, UnknownTimeZoneError
from app.services.email_queue_service import enqueue_email

def handle_session_start_use_case(data):
    try:
        print("Inicio activado", flush=True)
        is_valid, errors = validate_webhook_data(data)
        if not is_valid:
            raise ValueError(f"Invalid payload: {errors}")

        # Procesar usuario
        user_info = map_webhook_user_to_user_entity(data)
        external_user_id = user_info["ExternalUserId"]
        existing_user = User.query.filter_by(external_user_id=external_user_id).first()

        if existing_user:
            existing_user.name = user_info['name']
            existing_user.enable = user_info['enable']
            existing_user.disabled_time = user_info['disabledTime']
        else:
            new_user = User(
                external_user_id=external_user_id,
                name=user_info['name'],
                email=user_info['email'],
                hours_per_month=user_info['hoursPerMonth'],
                enable=user_info['enable'],
                disabled_time=user_info['disabledTime']
            )
            db.session.add(new_user)
            db.session.flush()
            existing_user = new_user
        # Validar si sesión ya existe
        external_id = data.get("id")
        existing_session = Session.query.filter_by(external_sesion_id=external_id).first()
        if existing_session:
            if existing_user.indNotificar:
                # Enviar correo de error por intento duplicado
                try:
                    tz = timezone(data.get("timeZone", "UTC"))
                except UnknownTimeZoneError:
                    tz = timezone("UTC")

                enqueue_email(
                    subject=f"Clockify - ERROR: Sesión ya existe - {existing_user.name} - ({datetime.now(tz).strftime('%Y-%m-%d %H:%M')})",
                    data=(
                        f"""
    <html>
    <body style="font-family: Arial, sans-serif; color: #333;">
      <div style="background-color: #ffebee; padding: 10px; font-size: 20px; font-weight: bold; color: #c62828; border-left: 6px solid #c62828;">
        ❌ ERROR: SESIÓN YA EXISTE
      </div>
    
      <p><strong style="color: #b71c1c;">👤 Usuario:</strong> {existing_user.name} ({existing_user.email})</p>
      <p><strong style="color: #b71c1c;">🔗 Sesión ID externa:</strong> {external_id}</p>
      <p><strong style="color: #b71c1c;">📝 Descripción:</strong> {existing_session.description or 'Sin descripción'}</p>
      <p><strong style="color: #b71c1c;">📁 Proyecto:</strong> {existing_session.projectName or 'Sin proyecto'}</p>
      <p><strong style="color: #b71c1c;">📌 Tarea:</strong> {existing_session.taskName or 'Sin tarea'}</p>
    
      <div style="background-color: #ffebee; padding: 10px; border-left: 6px solid #c62828; color: #b71c1c; margin-top: 20px;">
        Este error indica que se intentó <strong>iniciar una sesión que ya existe</strong> en el sistema.
        Es probable que Clockify haya enviado el mismo webhook dos veces por error.
      </div>
    </body>
    </html>
    """
                    ), to_address=existing_user.email
                )
            raise ValueError(f"Session with external ID {external_id} already exists on session start")

        # Crear sesión nueva
        session_data = map_webhook_to_session_entity(data)
        session_data["idUser"] = existing_user.id
        session_data["status"] = "APROBADO"
        session_data["observation"] = ""
        session_data["ValidDuration"] = None
        new_session = Session(**session_data)
        if not new_session.ValidStartDate:
            new_session.ValidStartDate = new_session.startDate
        db.session.add(new_session)
        db.session.flush()
        # Guardar en bitácora
        binnacle_data = map_session_to_binnacle_data(new_session)
        db.session.add(SessionBinnacle(**binnacle_data))
        db.session.commit()
        if existing_user.indNotificar:
            zoned_start = data.get("timeInterval", {}).get("zonedStart")
            try:
                tz = timezone(new_session.timeZone)
            except UnknownTimeZoneError:
                tz = timezone("UTC")
            # Enviar correo de confirmación
            enqueue_email(
                subject=f"Clockify - Sesión iniciada correctamente - {existing_user.name} - ({datetime.now(tz).strftime('%Y-%m-%d %H:%M')})",
                data=(
                    f"""
    <html>
    <body style="font-family: Arial, sans-serif; color: #333;">
      <div style="background-color: #e8f5e9; padding: 10px; font-size: 20px; font-weight: bold; color: #2e7d32; border-left: 6px solid #2e7d32;">
        ✅ SESIÓN INICIADA CORRECTAMENTE
      </div>
    
      <p><strong style="color: #1b5e20;">👤 Usuario:</strong> {existing_user.name} ({existing_user.email})</p>
      <p><strong style="color: #1b5e20;">🔗 Sesión ID externa:</strong> {external_id}</p>
      <p><strong style="color: #1b5e20;">📝 Descripción:</strong> {new_session.description or 'Sin descripción'}</p>
      <p><strong style="color: #1b5e20;">📁 Proyecto:</strong> {new_session.projectName or 'Sin proyecto'}</p>
      <p><strong style="color: #1b5e20;">📌 Tarea:</strong> {new_session.taskName or 'Sin tarea'}</p>
    
      <hr style="border:1px dotted black" />
    
      <p><strong style="color: #1b5e20;">📆 Inicio (UTC registrado):</strong> <code>{new_session.startDate}</code></p>
      <p><strong style="color: #1b5e20;">📆 Inicio (reloj del usuario):</strong> <code>{zoned_start or 'N/A'}</code></p>
    
      <div style="background-color: #f1f8e9; padding: 10px; border-left: 6px solid #7cb342; color: #33691e; margin-top: 20px;">
        La sesión ha sido registrada exitosamente y está activa.
      </div>
    </body>
    </html>
    """
                ),
                to_address=existing_user.email
            )

        return {
            "message": "Session started successfully",
            "sessionId": new_session.idSesion,
            "userId": existing_user.id
        }

    except ValueError as e:
        db.session.rollback()
        log_error_use_case(
            endpoint="/api-clockify/webhook/start",
            method="POST",
            error=e,
            payload=data,
            response_code=422
        )
        raise
    except Exception as e:
        db.session.rollback()
        log_error_use_case(
            endpoint="/api-clockify/webhook/start",
            method="POST",
            error=e,
            payload=data,
            response_code=500
        )
        raise
