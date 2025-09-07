import base64
from calendar import monthrange
from datetime import datetime, timedelta, UTC
import pandas as pd
from app.models.session import Session
from app.models.user import User
from flask import jsonify
from app.extensions import db
from app.services.email_queue_service import enqueue_email
from app.use_cases.manage_error_log import log_error_use_case
from io import BytesIO
from app.services.utility.sanitize_filename import sanitize_filename
from app.services.utility.get_local_time import get_local_time
from app.services.utility.format_duration_to_decimal import format_duration, format_duration_as_hms

EXCLUDED_FIELDS = [
    'idSesion', 'ExternalSesionId', 'idUser', 'idProject', 'idWorkspace', 'idTask',
    'offsetStart', 'offsetEnd', 'enable', 'disableTime'
]

def get_session_data_as_excel(sessions, user, report_type, start, end):
    try:
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
                "Fecha de fin (UTC)": end_date.strftime("%Y-%m-%dT%H:%M:%S") if end_date else None,
                "Fecha de fin (usuario)": end_local.strftime("%Y-%m-%dT%H:%M:%S") if end_local else None,
                "Fecha de inicio valida (UTC)": s.ValidStartDate.strftime(
                    "%Y-%m-%dT%H:%M:%S") if s.ValidStartDate else None,
                "Fecha de inicio valida (usuario)": valid_start_local.strftime(
                    "%Y-%m-%dT%H:%M:%S") if valid_start_local else None,
                "Fecha de fin valida (UTC)": valid_end_date.strftime("%Y-%m-%dT%H:%M:%S") if valid_end_date else None,
                "Fecha de fin valida (usuario)": valid_end_local.strftime(
                    "%Y-%m-%dT%H:%M:%S") if valid_end_local else None,
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

        now_str = datetime.now().strftime('%Y%m%d_%H%M%S')
        safe_username = sanitize_filename(user.name)
        filename = f"reporte_{safe_username}_{now_str}.xlsx"

        subject = f"Reporte {'mensual' if report_type.upper() == 'MONTHLY' else 'semanal'} de Clockify - {user.name}"
        body = f"""
<html>
  <body style="font-family: Arial, sans-serif; color: #333;">
    <p>Hola <strong>{user.name}</strong>,</p>

    <p>
      Adjunto encontrará el reporte <strong>{'mensual' if report_type.upper() == 'MONTHLY' else 'semanal'}</strong>
      de sus sesiones registradas entre el <strong>{start.date()}</strong> y el <strong>{end.date()}</strong>.
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
            to_address=user.email,
            attachments=[{
                "filename": filename,
                "content_bytes": encoded_content,
                "mime_type": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            }]
        )
    except ValueError as e:
        db.session.rollback()
        log_error_use_case(
            endpoint=f"/report/{report_type}",
            method="SYSTEM",
            error=e,
            payload={"user": user.email, "start": str(start), "end": str(end)},
            response_code=422
        )
        raise
    except Exception as e:
        log_error_use_case(
            endpoint=f"/report/{report_type}",
            method="SYSTEM",
            error=e,
            payload={"user": user.email, "start": str(start), "end": str(end)},
            response_code=500
        )
        raise e

def calculate_report_range(report_type: str, month: int = None, year: int = None, start_date: str = None):
    now = datetime.now(UTC)

    if report_type == "monthly":
        if not month or not (1 <= month <= 12):
            raise ValueError("Para el reporte mensual se debe proporcionar un mes válido (1-12).")

        year = year or now.year
        start_date_obj = datetime(year, month, 1, tzinfo=UTC)

        # Último día del mes
        last_day = monthrange(year, month)[1]
        end_date = datetime(year, month, last_day, 23, 59, 59, tzinfo=UTC)



    elif report_type == "weekly":
        if start_date:
            if isinstance(start_date, datetime):
                start_date_obj = start_date.replace(tzinfo=UTC).replace(hour=0, minute=0, second=0, microsecond=0)
            elif isinstance(start_date, str):
                start_date_obj = datetime.strptime(start_date, "%Y-%m-%d").replace(tzinfo=UTC, hour=0, minute=0, second=0, microsecond=0)
            else:
                raise ValueError("start_date debe ser un string 'YYYY-MM-DD' o un datetime.")
        else:
            # Recuerden que la semana laboral va de sábado a viernes
            start_date_obj = now.replace(hour=0, minute=0, second=0, microsecond=0)
        end_date = (start_date_obj + timedelta(days=6)).replace(hour=23, minute=59, second=59, microsecond=0)
    else:

        raise ValueError("Tipo de reporte inválido. Debe ser 'weekly' o 'monthly'.")

    return start_date_obj, end_date

def send_periodic_report(report_type="weekly", month=None, year=None, start_date=None):
    try:
        now = datetime.now(UTC)
        report_type = report_type.lower()
        if report_type not in ["weekly", "monthly"]:
            raise ValueError("Tipo de reporte inválido. Debe ser 'weekly' o 'monthly'.")
        # Usar mes actual si es mensual y no se proporcionó mes
        if report_type == "monthly" and month is None:
            month = now.month
        # Convertir parámetros si vienen como string desde el controlador
        if month is not None:
            try:
                month = int(month)
            except ValueError:
                raise ValueError("El mes debe ser un número entero (1-12).")

        if year is not None:
            try:
                year = int(year)
            except ValueError:
                raise ValueError("El año debe ser un número entero.")
        if report_type == "weekly" and start_date:
            try:
                # Se espera formato 'YYYY-MM-DD'
                parsed_date = datetime.strptime(start_date, "%Y-%m-%d").replace(tzinfo=UTC)
                start_date = parsed_date
            except ValueError:
                raise ValueError("La fecha para el reporte semanal debe estar en formato 'YYYY-MM-DD'.")
        # Si se pasó start_date como string, se intenta convertir a datetime
        if isinstance(start_date, str):
            start_date = datetime.fromisoformat(start_date)

        start_date, end_date = calculate_report_range(
            report_type=report_type,
            month=month,
            year=year,
            start_date=start_date
        )

        users = User.query.filter_by(enable=True, indNotificar=True).all()

        for user in users:
            try:
                sessions = (
                    Session.query
                    .filter(
                        Session.idUser == user.id,
                        Session.startDate >= start_date,
                        Session.startDate <= end_date,
                        Session.enable == True
                    )
                    .order_by(Session.startDate.asc())
                    .all()
                )

                if sessions:
                    get_session_data_as_excel(sessions, user, report_type, start_date, end_date)
            except ValueError as e:
                db.session.rollback()
                log_error_use_case(
                    endpoint=f"/report/{report_type}",
                    method="SYSTEM",
                    error=e,
                    payload={"user_id": user.id, "email": user.email},
                    response_code=422
                )
                raise
            except Exception as user_e:
                log_error_use_case(
                    endpoint=f"/report/{report_type}",
                    method="SYSTEM",
                    error=user_e,
                    payload={"user_id": user.id, "email": user.email},
                    response_code=500
                )
                raise

    except ValueError as e:
        db.session.rollback()
        log_error_use_case(
            endpoint=f"/report/{report_type}",
            method="POST",
            error=e,
            payload={"report_type":report_type},
            response_code=422
        )
        raise
    except Exception as general_e:
        log_error_use_case(
            endpoint=f"/report/{report_type}",
            method="SYSTEM",
            error=general_e,
            payload={"message": "Unexpected failure in send_periodic_report"},
            response_code=500
        )
        raise

