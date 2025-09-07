from datetime import datetime

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
from pytz import timezone, UnknownTimeZoneError
from app.services.mail_service_manual import send_webhook_email
#MIRAR SI AL CERRAR POR EDITAR YA ESTA OVERTIME, EDITAN SESIONES ABIERTAS
def process_webhook_use_case(data):
    try:
        print("Edicion activada")
        is_valid, errors = validate_webhook_data(data)
        if not is_valid:
            raise ValueError(f"Invalid payload: {errors}")

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

        existing_user.name = user_info["name"]
        existing_user.enable = user_info["enable"]
        existing_user.disabled_time = user_info["disabledTime"]

        # --- Procesar sesion ---
        external_id = data.get("id")
        existing_session = Session.query.filter_by(external_sesion_id=external_id).first()

        # Si la sesion no existe crearla
        if not existing_session:
            session_data = map_webhook_to_session_entity(data)
            session_data["idUser"] = existing_user.id
            session_data["status"] = "APROBADO"
            session_data["observation"] = ""
            new_session = Session(**session_data)
            if new_session.duration and new_session.duration.total_seconds() > 5 * 3600:
                new_session.overtime = True
            db.session.add(new_session)
            db.session.flush()

            db.session.add(SessionBinnacle(**map_session_to_binnacle_data(new_session)))
            db.session.commit()
            if existing_user.indNotificar:
                # --- Formatear fechas para correo ---
                try:
                    tz = timezone(new_session.timeZone)
                except UnknownTimeZoneError:
                    tz = timezone("UTC")

                zoned_start = data.get("timeInterval", {}).get("zonedStart")
                zoned_end = data.get("timeInterval", {}).get("zonedEnd")
                send_webhook_email(
                    subject=f"Clockify - Reporte de creación de jornada desde edición - {existing_user.name} - ({datetime.now(tz).strftime('%Y-%m-%d %H:%M')})",
                    data=f"""
    <html>
      <body style="font-family: Arial, sans-serif; color: #333;">
        <div style="background-color: #e3f2fd; padding: 10px; font-size: 20px; font-weight: bold; color: #1565c0; border-left: 6px solid #1565c0;">
          📌 SESIÓN CREADA AUTOMÁTICAMENTE DESDE EDICIÓN (NO EXISTIA ANTES)
        </div>
    
        <p><strong style="color: #0d47a1;">👤 Usuario:</strong> {existing_user.name} ({existing_user.email})</p>
        <p><strong style="color: #0d47a1;">🔗 Sesión ID externa:</strong> {external_id}</p>
        <p><strong style="color: #0d47a1;">📝 Descripción:</strong> {new_session.description or 'Sin descripción'}</p>
        <p><strong style="color: #0d47a1;">📁 Proyecto:</strong> {new_session.projectName or 'Sin proyecto'}</p>
        <p><strong style="color: #0d47a1;">📌 Tarea:</strong> {new_session.taskName or 'Sin tarea'}</p>
    
        <hr style="border:1px dotted black" />
    
        <p><strong style="color: #0d47a1;">📆 Inicio (UTC registrado):</strong> {new_session.startDate}</p>
        <p><strong style="color: #0d47a1;">🕒 Inicio (reloj del usuario):</strong> <code>{zoned_start or 'N/A'}</code></p>
        <p><strong style="color: #0d47a1;">📆 Fin (UTC registrado):</strong> <code>{new_session.endDate if new_session.endDate else 'N/A'}</code></p>
        <p><strong style="color: #0d47a1;">🕒 Fin (reloj del usuario):</strong> <code>{zoned_end or 'N/A'}</code></p>
        <p><strong style="color: #0d47a1;">⏱️ Duración:</strong> {new_session.duration}</p>
        <p><strong style="color: #0d47a1;">⏰ Overtime:</strong> {'Sí' if new_session.overtime else 'No'}</p>
    
        <div style="background-color: #fff8e1; padding: 10px; border-left: 6px solid #ffb300; color: #ff6f00; margin-top: 20px;">
          Esta sesión fue registrada desde un <strong>webhook de edición</strong>, pero no se encontró previamente en el sistema.<br>
        </div>
      </body>
    </html>
    """,
                    user_email=existing_user.email
                )
            return {"message": "Session created automatically and logged"}

        session_data = map_webhook_to_session_entity(data)
        session_data["idUser"] = existing_user.id
        # Mantener los campos válidos anteriores
        debe_reportarse = False
        actualizo_valids = False
        correo_body = ""

        # Verificar cambio de duración (en sesiones cerradas)
        if not existing_session.currentlyRunning and session_data["duration"]:
            duration_old = existing_session.duration.total_seconds() if existing_session.duration else 0
            duration_new = session_data["duration"].total_seconds()
            diff_minutes = abs(duration_old - duration_new) / 60
            existing_session.overtime = duration_new > 5 * 3600
            if duration_old != duration_new:
                existing_session.updatingQuantity += 1
                # Actualizar valids si cumple condiciones
                if existing_session.updatingQuantity < 2 and diff_minutes < 5:
                    existing_session.ValidEndDate = session_data["endDate"]
                    existing_session.ValidDuration = session_data["duration"]
                    actualizo_valids = True
                else:
                    debe_reportarse = True
                    existing_session.status = "EN OBSERVACION"

        # Verificar cambio de hora en sesiones abiertas
        if existing_session.currentlyRunning:
            start_old = existing_session.startDate
            start_new = session_data.get("startDate")
            if start_old and start_new and start_old != start_new:
                diff_minutes = abs((start_old - start_new).total_seconds()) / 60
                existing_session.updatingQuantity += 1
                if existing_session.updatingQuantity < 2 and diff_minutes < 5:
                    existing_session.ValidStartDate = session_data["startDate"]
                    actualizo_valids = True
                else:
                    debe_reportarse = True
                    existing_session.status = "EN OBSERVACION"
        if debe_reportarse:
            try:
                tz = timezone(existing_session.timeZone)
            except UnknownTimeZoneError:
                tz = timezone("UTC")

            start_old_local = existing_session.startDate.astimezone(tz) if existing_session.startDate else None
            start_new_local = session_data["startDate"].astimezone(tz) if session_data["startDate"] else None
            end_old_local = existing_session.endDate.astimezone(tz) if existing_session.endDate else None
            end_new_local = session_data["endDate"].astimezone(tz) if session_data["endDate"] else None
            correo_body = f"""
<html>
<body style="font-family: Arial, sans-serif; color: #333;">
<div style="background-color: #e0f7fa; padding: 10px; font-size: 20px; font-weight: bold; color: #00695c; border-left: 6px solid #00695c;">
      ⚠️ CAMBIO DETECTADO
</div>
 
    <p><strong style="color: #00796b;">👤 Usuario:</strong> {existing_user.name} ({existing_user.email})</p>
<p><strong style="color: #00796b;">🔗 Sesión ID externa:</strong> {external_id}</p>
<p><strong style="color: #00796b;">📝 Descripción:</strong> {existing_session.description}</p>
<p><strong style="color: #00796b;">📁 Proyecto:</strong> {existing_session.projectName}</p>
<p><strong style="color: #00796b;">📌 Tarea:</strong> {existing_session.taskName}</p>
 
    <hr style="border:1px dotted black" />
 
    <p><strong style="color: #00796b;">📆 Inicio original (Reloj Usuario):</strong> <code>{start_old_local.strftime('%Y-%m-%d %H:%M:%S %Z') if start_old_local else 'N/A'}</code></p>
<p><strong style="color: #00796b;">📆 Inicio nuevo (Reloj Usuario):</strong> <code>{start_new_local.strftime('%Y-%m-%d %H:%M:%S %Z') if start_new_local else 'N/A'}</code></p>
<p><strong style="color: #00796b;">📆 Fin original (Reloj Usuario):</strong> <code>{end_old_local.strftime('%Y-%m-%d %H:%M:%S %Z') if end_old_local else 'N/A'}</code></p>
<p><strong style="color: #00796b;">📆 Fin nuevo (Reloj Usuario):</strong> <code>{end_new_local.strftime('%Y-%m-%d %H:%M:%S %Z') if end_new_local else 'N/A'}</code></p>

<p><strong style="color: #00796b;">📆 Inicio original (UTC):</strong> <code>{existing_session.startDate if existing_session.startDate else 'N/A'}</code></p>
<p><strong style="color: #00796b;">📆 Inicio nuevo (UTC):</strong> <code>{session_data["startDate"] if session_data["startDate"] else 'N/A'}</code></p>
<p><strong style="color: #00796b;">📆 Fin original (UTC):</strong> <code>{existing_session.endDate if existing_session.endDate else 'N/A'}</code></p>
<p><strong style="color: #00796b;">📆 Fin nuevo (UTC):</strong> <code>{session_data["endDate"] if session_data["endDate"] else 'N/A'}</code></p>
 
    <hr style="border:1px dotted black" />
 
    <p><strong style="color: #00796b;">⏱️ Duración original:</strong> {existing_session.duration}</p>
<p><strong style="color: #00796b;">⏱️ Duración nueva:</strong> {session_data['duration']}</p>
<p><strong style="color: #00796b;">🔁 Ediciones totales:</strong> {existing_session.updatingQuantity}</p>
<p><strong style="color: #00796b;">⏰ Overtime:</strong> {'Sí' if existing_session.overtime else 'No'}</p>
 
    <div style="background-color: #fff3e0; padding: 10px; border-left: 6px solid #f57c00; color: #e65100; margin-top: 20px;">
      ⚠️ Recuerde que modificar los tiempos de la sesión <strong>no está permitido</strong>, y esta acción será <strong>notificada</strong> y <strong>reportada</strong>.
</div>
 
  </body>
</html>
"""



        # Actualizar sesion
        for key, value in session_data.items():
            if key in ["ValidStartDate", "ValidEndDate", "ValidDuration"] and not actualizo_valids:
                continue
            if hasattr(existing_session, key):
                setattr(existing_session, key, value)
        #binnacle
        db.session.add(SessionBinnacle(**map_session_to_binnacle_data(existing_session)))
        db.session.commit()

        if debe_reportarse:
            if existing_user.indNotificar:
                send_webhook_email(
                    subject=f"Clockify - ALERTA: EDICIÓN de sesión Clockify REPORTE - {existing_user.name} - ({datetime.now(tz).strftime('%Y-%m-%d %H:%M')})",
                    data=correo_body,
                    user_email=existing_user.email
                )

        return {"message": "Session updated and logged"}

    except ValueError as e:
        db.session.rollback()
        log_error_use_case(
            endpoint="/api-clockify/webhook/edit",
            method="POST",
            error=e,
            payload=data,
            response_code=422
        )
        raise
    except Exception as e:
        db.session.rollback()
        log_error_use_case(
            endpoint="/api-clockify/webhook/edit",
            method="POST",
            error=e,
            payload=data,
            response_code=500
        )
        raise e