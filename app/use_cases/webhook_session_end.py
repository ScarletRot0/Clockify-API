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


def handle_session_end_use_case(data):
    try:
        # Validación inicial
        print("Finalizacion activada")
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

        # Buscar sesion existente
        external_id = data.get("id")
        session = Session.query.filter_by(external_sesion_id=external_id).first()

        # Si la sesión no existe, crearla directamente
        if not session:
            session_data = map_webhook_to_session_entity(data)
            session_data["idUser"] = existing_user.id
            session_data["status"] = "APROBADO"
            session_data["observation"] = ""
            new_session = Session(**session_data)
            db.session.add(new_session)
            db.session.flush()
            if new_session.duration and new_session.duration.total_seconds() > 5 * 3600:
                new_session.overtime = True
            db.session.add(SessionBinnacle(**map_session_to_binnacle_data(new_session)))
            db.session.commit()
            if existing_user.indNotificar:
                # Formatear fechas para correo
                try:
                    tz = timezone(new_session.timeZone)
                except UnknownTimeZoneError:
                    tz = timezone("UTC")


                zoned_start = data.get("timeInterval", {}).get("zonedStart")
                zoned_end = data.get("timeInterval", {}).get("zonedEnd")
                enqueue_email(
                    subject=f"Clockify - Sesión creada desde cierre (no existía) - {existing_user.name} - ({datetime.now(tz).strftime('%Y-%m-%d %H:%M')})",
                    data=f"""<html>
    <body style="font-family: Arial, sans-serif; color: #333;">
      <div style="background-color: #ffebee; padding: 10px; font-size: 20px; font-weight: bold; color: #c62828; border-left: 6px solid #c62828;">
        ❌ ERROR: SESIÓN NO ENCONTRADA EN CIERRE
      </div>
    
      <p><strong style="color: #b71c1c;">👤 Usuario:</strong> {existing_user.name} ({existing_user.email})</p>
      <p><strong style="color: #b71c1c;">🔗 Sesión ID externa:</strong> {external_id}</p>
      <p><strong style="color: #b71c1c;">📝 Descripción:</strong> {data.get('description', 'No proporcionada')}</p>
      <p><strong style="color: #b71c1c;">📁 Proyecto:</strong> {data.get('projectName', 'Sin proyecto')}</p>
      <p><strong style="color: #b71c1c;">📌 Tarea:</strong> {data.get('taskName', 'Sin tarea')}</p>
      <p><strong style="color: #33691e;">📆 Inicio (UTC):</strong> <code>{new_session.startDate if new_session.startDate else 'N/A'}</code></p>
      <p><strong style="color: #33691e;">📆 Inicio (usuario):</strong> <code>{zoned_start or 'N/A'}</code></p>
      <p><strong style="color: #33691e;">📆 Fin válido (UTC):</strong> <code>{new_session.endDate if new_session.endDate else 'N/A'}</code></p>
      <p><strong style="color: #33691e;">📆 Fin (usuario):</strong> <code>{zoned_end or 'N/A'}</code></p>
    
      <div style="background-color: #ffebee; padding: 10px; border-left: 6px solid #c62828; color: #b71c1c; margin-top: 20px;">
        Este error indica que se intentó cerrar una sesión que <strong>no ha sido iniciada correctamente</strong> o ya fue cerrada y deshabilitada.
      </div>
    </body>
    </html>""",
                    to_address=existing_user.email
                )
            return {"message": "Session created automatically on end and logged"}

        # Actualizar sesion con nuevos datos de fin
        session_data = map_webhook_to_session_entity(data)
        session_data["idUser"] = existing_user.id

        if not session.ValidStartDate and session.status == "APROBADO":
            session.ValidStartDate = session.startDate

        if not session.ValidEndDate:
            session.ValidEndDate = session_data.get("endDate")

        if not session.ValidDuration and session.ValidStartDate and session_data.get("endDate"):
            session.ValidDuration = session_data["endDate"] - session.ValidStartDate
        # Asegurar que se guarde el endDate antes del for
        if session.endDate is None and session_data.get("endDate"):
            session.endDate = session_data["endDate"]
        for key, value in session_data.items():
            if key in ["ValidStartDate", "ValidEndDate", "ValidDuration", "endDate"]:
                continue  #estos ya se manejaron arriba
            if hasattr(session, key):
                setattr(session, key, value)
        if session.duration and session.duration.total_seconds() > 5 * 3600:
            session.overtime = True
        #bitacora
        db.session.add(SessionBinnacle(**map_session_to_binnacle_data(session)))
        db.session.commit()
        if existing_user.indNotificar:
            # Enviar correo de confirmación de cierre
            try:
                tz = timezone(session.timeZone)
            except UnknownTimeZoneError:
                tz = timezone("UTC")

            zoned_start = data.get("timeInterval", {}).get("zonedStart")
            zoned_end = data.get("timeInterval", {}).get("zonedEnd")
            valid_start_local = session.ValidStartDate.astimezone(tz) if session.ValidStartDate else None
            valid_end_local = session.ValidEndDate.astimezone(tz) if session.ValidEndDate else None
            # Enviar correo de confirmación
            body  = f"""
    <html>
    <body style="font-family: Arial, sans-serif; color: #333;">
      <div style="background-color: #dcedc8; padding: 10px; font-size: 20px; font-weight: bold; color: #33691e; border-left: 6px solid #33691e;">
        ✅ SESIÓN FINALIZADA
      </div>
    
      <p><strong style="color: #33691e;">👤 Usuario:</strong> {existing_user.name} ({existing_user.email})</p>
      <p><strong style="color: #33691e;">🔗 ID externa:</strong> {external_id}</p>
      <p><strong style="color: #33691e;">📁 Proyecto:</strong> {session.projectName}</p>
      <p><strong style="color: #33691e;">📌 Tarea:</strong> {session.taskName}</p>
      <p><strong style="color: #33691e;">📝 Descripción:</strong> {session.description}</p>
    
      <hr style="border:1px dotted black" />
    
      <p><strong style="color: #33691e;">📆 Inicio válido (UTC):</strong> <code>{session.ValidStartDate or 'N/A'}</code></p>
      <p><strong style="color: #33691e;">📆 Inicio válido (usuario):</strong> <code>{valid_start_local.strftime('%Y-%m-%d %H:%M:%S %Z') if valid_start_local else 'N/A'}</code></p>
      <p><strong style="color: #33691e;">📆 Inicio registrado (usuario):</strong> <code>{zoned_start or 'N/A'}</code></p>
      <p><strong style="color: #33691e;">📆 Inicio registrado (UTC):</strong> <code>{session.startDate or 'N/A'}</code></p>
    
      <p><strong style="color: #33691e;">📆 Fin válido (UTC):</strong> <code>{session.ValidEndDate or 'N/A'}</code></p>
      <p><strong style="color: #33691e;">📆 Fin válido (usuario):</strong> <code>{valid_end_local.strftime('%Y-%m-%d %H:%M:%S %Z') if valid_end_local else 'N/A'}</code></p>
      <p><strong style="color: #33691e;">📆 Fin registrado (usuario):</strong> <code>{zoned_end or 'N/A'}</code></p>
      <p><strong style="color: #33691e;">📆 Fin registrado (UTC):</strong> <code>{session.endDate or 'N/A'}</code></p>
    
      <hr style="border:1px dotted black" />
    
      <p><strong style="color: #33691e;">⏱️ Duración válida:</strong> {session.ValidDuration}</p>
      <p><strong style="color: #33691e;">⏰ Overtime:</strong> {'Sí' if session.overtime else 'No'}</p>
    
      <div style="background-color: #f1f8e9; padding: 10px; border-left: 6px solid #8bc34a; color: #33691e; margin-top: 20px;">
        La sesión ha sido registrada exitosamente tras su finalización.
      </div>
    </body>
    </html>
    """
            enqueue_email(
                subject=f"Clockify - Sesion Finalizada - {existing_user.name} - ({datetime.now(tz).strftime('%Y-%m-%d %H:%M')})",
                data=body,
                to_address=existing_user.email
            )

        return {"message": "Session ended successfully and logged in binnacle"}

    except ValueError as e:
        db.session.rollback()
        log_error_use_case(
            endpoint="/api-clockify/webhook/end",
            method="POST",
            error=e,
            payload=data,
            response_code=422
        )
        raise
    except LookupError as e:
        db.session.rollback()
        log_error_use_case(
            endpoint="/api-clockify/webhook/end",
            method="POST",
            error=e,
            payload=data,
            response_code=404
        )
        raise
    except Exception as e:
        db.session.rollback()
        log_error_use_case(
            endpoint="/api-clockify/webhook/end",
            method="POST",
            error=e,
            payload=data,
            response_code=500
        )
        raise e
