import base64
from datetime import datetime, UTC
from io import BytesIO
import pandas as pd
from flask import jsonify
from app.models.session import Session
from app.models.user import User
from app.services.email_queue_service import enqueue_email
from app.use_cases.manage_error_log import log_error_use_case
from app.validators.date_validator import parse_date_param
from app.services.utility.sanitize_filename import sanitize_filename
from app.services.utility.get_local_time import get_local_time
from app.services.utility.format_duration_to_decimal import format_duration, format_duration_as_hms

EXCLUDED_FIELDS = [
    'idSesion', 'ExternalSesionId', 'idUser', 'idProject', 'idWorkspace', 'idTask',
    'offsetStart', 'offsetEnd', 'enable', 'disableTime'
]
def send_user_report_use_case(id_user, start_date_str, end_date_str, email_to_send):
    try:
        print("[INFO] Validando fechas...")
        start_iso, start_error = parse_date_param(start_date_str, "startDate")
        end_iso, end_error = parse_date_param(end_date_str, "endDate")

        if start_error:
            raise  ValueError(f"error: Invalid date format for 'startDate'")  # retorna JSON y 400 directamente
        if end_error:
            raise ValueError(f"error: Invalid date format for 'endDate'")
        start_date = datetime.fromisoformat(start_iso).replace(hour=0, minute=0, second=0)
        end_date = datetime.fromisoformat(end_iso).replace(hour=23, minute=59, second=59)

        print(f"[INFO] Fechas validadas: {start_date} a {end_date}")

        print(f"[INFO] Buscando usuario con ID {id_user}...")
        user = User.query.get(id_user)
        if not user:
            raise LookupError(f"No se encontró el usuario con id: {id_user}")
        print(f"[INFO] Usuario encontrado: {user.name} ({user.email})")

        print("[INFO] Consultando sesiones del usuario en el rango dado...")
        sessions = (
            Session.query
            .filter(
                Session.idUser == id_user,
                Session.startDate >= start_date,
                Session.startDate <= end_date,
                Session.enable == True
            )
            .order_by(Session.startDate.asc())
            .all()
        )
        print(f"[INFO] Se encontraron {len(sessions)} sesiones")

        if not sessions:
            raise LookupError(f"El usuario no tiene sesiones entre {start_date_str} y {end_date_str}")

        print("[INFO] Preparando datos para el Excel...")
        data = []
        for s in sessions:
            now = datetime.now(UTC)
            end_date = s.endDate or now
            valid_end_date = s.ValidEndDate or now
            duration = s.duration or (
                (end_date - s.startDate) if s.startDate else None
            )
            valid_duration = s.ValidDuration or (
                (valid_end_date - s.ValidStartDate) if s.ValidStartDate else None
            )

            # Calcular fechas con offset
            start_local = get_local_time(s.startDate, s.offsetStart)
            end_local = get_local_time(end_date, s.offsetEnd)
            valid_start_local = get_local_time(s.ValidStartDate, s.offsetStart)
            valid_end_local = get_local_time(valid_end_date, s.offsetEnd)

            row = {
                "Descripcion": s.description,
                "Nombre del proyecto": s.projectName,
                "Nombre de la tarea": s.taskName,
                "Fecha de inicio (UTC)": s.startDate.strftime("%Y-%m-%dT%H:%M:%S") if s.startDate else None,
                "Fecha de inicio (usuario)": start_local.strftime("%Y-%m-%dT%H:%M:%S") if start_local else None,
                "Fecha de fin (UTC)": end_date.strftime("%Y-%m-%dT%H:%M:%S") if isinstance(end_date, datetime) else None,
                "Fecha de fin (usuario)": end_local.strftime("%Y-%m-%dT%H:%M:%S") if isinstance(end_local, datetime) else None,
                "Fecha de inicio valida (UTC)": s.ValidStartDate.strftime(
                    "%Y-%m-%dT%H:%M:%S") if s.ValidStartDate else None,
                "Fecha de inicio valida (usuario)": valid_start_local.strftime(
                    "%Y-%m-%dT%H:%M:%S") if valid_start_local else None,
                "Fecha de fin valida (UTC)": valid_end_date.strftime("%Y-%m-%dT%H:%M:%S") if isinstance(valid_end_date, datetime) else None,
                "Fecha de fin valida (usuario)": valid_end_local.strftime(
                    "%Y-%m-%dT%H:%M:%S") if isinstance(valid_end_local,datetime) else None,
                "Duracion": format_duration_as_hms(duration),
                "Duracion valida": format_duration_as_hms(valid_duration),
                "Duracion(decimal)": format_duration(duration),
                "Duracion valida(decimal)": format_duration(valid_duration),
                "Zona Horaria": s.timeZone,
                "En curso": s.currentlyRunning,
                "Overtime": s.overtime,
                "Modificaciones": s.updatingQuantity,
                "Estado": s.status,
                "Observacion": s.observation
            }
            data.append(row)

        df = pd.DataFrame(data)
        # Convertir a float las columnas de duración decimal
        df["Duracion(decimal)"] = pd.to_numeric(df["Duracion(decimal)"], errors="coerce")
        df["Duracion valida(decimal)"] = pd.to_numeric(df["Duracion valida(decimal)"], errors="coerce")

        # Calcular totales
        total_duration = df["Duracion(decimal)"].sum()
        total_valid_duration = df["Duracion valida(decimal)"].sum()

        # Crear fila de totales
        total_row = {col: "" for col in df.columns}
        total_row["Descripcion"] = "TOTALES"
        total_row["Duracion(decimal)"] = round(total_duration, 2)
        total_row["Duracion valida(decimal)"] = round(total_valid_duration, 2)

        # Agregar la fila de totales al final
        df = pd.concat([df, pd.DataFrame([total_row])], ignore_index=True)
        buffer = BytesIO()
        df.to_excel(buffer, index=False, engine='openpyxl')
        buffer.seek(0)

        safe_username = sanitize_filename(user.name)
        now_str = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"reporte_{safe_username}_{now_str}.xlsx"

        print("[INFO] Enviando correo con el Excel adjunto...")
        subject = f"Reporte personalizado Clockify - {user.name}"
        body = f"""
<html>
  <body style="font-family: Arial, sans-serif; color: #333;">
    <p>
      Adjunto encontrará el <strong>reporte personalizado</strong> de sesiones del usuario
      <strong>{user.name}</strong>.
    </p>
    <p>
      Período: <strong>{start_date.date()}</strong> a <strong>{end_date.date()}</strong><br/>
      Total de sesiones: <strong>{len(sessions)}</strong>
    </p>

    <p>Saludos cordiales,</p>
    <p><strong>Equipo de ActionTracker</strong></p>
  </body>
</html>
"""
        encoded_content = base64.b64encode(buffer.read()).decode("utf-8")
        enqueue_email(
            subject=subject,
            data=body,
            to_address=email_to_send,
            attachments=[{
                "filename": filename,
                "content_bytes": encoded_content,
                "mime_type": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            }]
        )
        print(f"[INFO] Reporte enviado correctamente a {email_to_send}")

        return {"message": "Reporte generado y enviado exitosamente"}

    except LookupError as e:
        log_error_use_case(
            endpoint="/sessions/api-clockify/reports/user",
            method="POST",
            error=e,
            payload={
                "idUser": id_user,
                "startDate": start_date_str,
                "endDate": end_date_str,
                "emailToSend": email_to_send
            },
            response_code=404
        )
        raise

    except ValueError as e:
        log_error_use_case(
            endpoint="/sessions/api-clockify/reports/user",
            method="POST",
            error=e,
            payload={
                "idUser": id_user,
                "startDate": start_date_str,
                "endDate": end_date_str,
                "emailToSend": email_to_send
            },
            response_code=422
        )
        raise

    except Exception as e:
        print("[ERROR] Ocurrió un error general en send_user_report_use_case")
        log_error_use_case(
            endpoint="/sessions/api-clockify/reports/user",
            method="POST",
            error=e,
            payload={
                "idUser": id_user,
                "startDate": start_date_str,
                "endDate": end_date_str,
                "emailToSend": email_to_send
            },
            response_code=500
        )
        raise e
