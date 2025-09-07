from app.mappers.webhook_mapper import (
    map_webhook_user_to_user_entity,
    map_webhook_to_session_entity,
    map_session_to_binnacle_data
)
from flask import jsonify
from app.models.user import User
from app.models.session import Session
from app.models.session_binnacle import SessionBinnacle
from app.use_cases.manage_error_log import log_error_use_case
from app.extensions import db
from app.validators.webhook_validator import validate_webhook_data
from app.services.email_queue_service import enqueue_email
from datetime import datetime, UTC
from pytz import timezone, UnknownTimeZoneError

def handle_session_delete_use_case(data):
    try:
        print("Borrado activado")
        is_valid, errors = validate_webhook_data(data)
        if not is_valid:
            raise ValueError(f"Invalid payload: {errors}")

        # --- Procesar usuario ---
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

        # --- Procesar sesión ---
        external_id = data.get("id")
        existing_session = Session.query.filter_by(external_sesion_id=external_id).first()
        try:
            tz = timezone(data.get("timeInterval", {}).get("timeZone", "UTC"))
        except UnknownTimeZoneError:
            tz = timezone("UTC")
        if existing_user.indNotificar:
            if not existing_session or existing_session.enable == False:
                session_data = map_webhook_to_session_entity(data)
                description = session_data.get("description", "Sin descripción")
                task_name = session_data.get("taskName", "Sin tarea")
                project_name = session_data.get("projectName", "Sin proyecto")

                error_message = f"""
                <html>
                  <body style="font-family: Arial, sans-serif; color: #333;">
                    <div style="background-color: #ffebee; padding: 10px; font-size: 20px; font-weight: bold; color: #c62828; border-left: 6px solid #c62828;">
                      ❌ ERROR: Intento de borrado inválido
                    </div>
    
                    <p><strong style="color: #b71c1c;">👤 Usuario:</strong> {existing_user.name} ({existing_user.email})</p>
                    <p><strong style="color: #b71c1c;">🔗 ID externa:</strong> {external_id}</p>
                    <p><strong style="color: #b71c1c;">📝 Descripción:</strong> {description}</p>
                    <p><strong style="color: #b71c1c;">📁 Proyecto:</strong> {project_name}</p>
                    <p><strong style="color: #b71c1c;">📌 Tarea:</strong> {task_name}</p>
    
                    <div style="background-color: #fce4ec; padding: 10px; border-left: 6px solid #ad1457; color: #880e4f; margin-top: 20px;">
                      Esta sesión <strong>no existe</strong> o ya fue <strong>eliminada previamente</strong> en la base de datos.
                    </div>
                  </body>
                </html>
                """

                enqueue_email(
                    subject=f"Clockify - ERROR: Sesión no encontrada en borrado - {existing_user.name} - ({datetime.now(tz).strftime('%Y-%m-%d %H:%M')}) ",
                    data=error_message,
                    to_address=existing_user.email
                )
            raise LookupError(f"Session with external ID {external_id} does not exist")

        # Actualizar sesion como inactiva
        existing_session.idUser = existing_user.id
        existing_session.enable = False
        existing_session.disableTime = datetime.now(UTC)

        # Guardar binnacle antes del commit
        db.session.add(SessionBinnacle(**map_session_to_binnacle_data(existing_session)))
        db.session.commit()
        if existing_user.indNotificar:
            local_start = existing_session.startDate.astimezone(tz)
            local_end = existing_session.endDate.astimezone(tz) if existing_session.endDate else None
            # Enviar correo de confirmación
            correo_body = f"""<html>
      <body style="font-family: Arial, sans-serif; color: #333;">
        <div style="background-color: #ffebee; padding: 10px; font-size: 20px; font-weight: bold; color: #c62828; border-left: 6px solid #c62828;">
          ❌ SESIÓN BORRADA
        </div>
    
        <p><strong style="color: #b71c1c;">👤 Usuario:</strong> {existing_user.name} ({existing_user.email})</p>
        <p><strong style="color: #b71c1c;">🔗 Sesión ID externa:</strong> {external_id}</p>
        <p><strong style="color: #b71c1c;">📝 Descripción:</strong> {existing_session.description}</p>
        <p><strong style="color: #b71c1c;">📁 Proyecto:</strong> {existing_session.projectName}</p>
        <p><strong style="color: #b71c1c;">📌 Tarea:</strong> {existing_session.taskName}</p>
    
        <hr style="border:1px dotted #c62828" />
    
        <p><strong style="color: #b71c1c;">📆 Inicio (Reloj Usuario):</strong> <code>{local_start.strftime('%Y-%m-%d %H:%M:%S %Z')}</code></p>
        <p><strong style="color: #b71c1c;">📆 Fin (Reloj Usuario):</strong> <code>{local_end.strftime('%Y-%m-%d %H:%M:%S %Z') if local_end else 'N/A'}</code></p>
        
        <p><strong style="color: #b71c1c;">📆 Inicio (UTC):</strong> <code>{existing_session.startDate}</code></p>
        <p><strong style="color: #b71c1c;">📆 Fin (UTC):</strong> <code>{existing_session.endDate if existing_session.endDate else 'N/A'}</code></p>
    
        <p><strong style="color: #b71c1c;">⏱️ Duración:</strong> {existing_session.duration}</p>
        <p><strong style="color: #b71c1c;">⏰ Overtime:</strong> {'Sí' if existing_session.overtime else 'No'}</p>
    
        <div style="background-color: #fce4ec; padding: 10px; border-left: 6px solid #ad1457; color: #880e4f; margin-top: 20px;">
          Esta sesión ha sido marcada como <strong>inactiva</strong> y no aparecerá en los reportes activos.
        </div>
      </body>
    </html>
    """

            enqueue_email(
                subject=f"Clockify - Confirmación de BORRADO de sesión Clockify - {existing_user.name} - ({datetime.now(tz).strftime('%Y-%m-%d %H:%M')})",
                data=correo_body, to_address=existing_user.email
            )

        return {"message": "Session deleted (disabled) and logged in binnacle"}

    except ValueError as e:
        db.session.rollback()
        log_error_use_case(
            endpoint="/api-clockify/webhook/delete",
            method="POST",
            error=e,
            payload=data,
            response_code=422
        )
        raise
    except LookupError as e:
        db.session.rollback()
        log_error_use_case(
            endpoint="/api-clockify/webhook/delete",
            method="POST",
            error=e,
            payload=data,
            response_code=404
        )
        raise
    except Exception as e:

        db.session.rollback()
        log_error_use_case(

            endpoint="/api-clockify/webhook/delete",
            method="POST",
            error=e,
            payload=data,
            response_code=500

        )
        raise e

