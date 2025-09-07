import time
from datetime import datetime, timedelta, UTC
from app.extensions import db
from app.models.session import Session
from app.models.session_binnacle import SessionBinnacle
from app.mappers.webhook_mapper import map_session_to_binnacle_data
from app.services.mail_service_manual import send_webhook_email
from app.use_cases.manage_error_log import log_error_use_case
from app.repositories.user_repository import get_user_by_id
from pytz import timezone, UnknownTimeZoneError
MAX_SESSION_SECONDS = 5 * 60 * 60  # 5 horas

def monitor_open_sessions(app):
    print("Iniciando monitoreo de sesiones abiertas", flush=True)

    while True:
        try:
            with app.app_context():
                now = datetime.now(UTC)
                open_sessions = Session.query.filter_by(currentlyRunning=True, enable=True).all()

                for session in open_sessions:
                    if not session.startDate:
                        continue

                    elapsed = (now - session.startDate).total_seconds()

                    if not session.overtime and elapsed > MAX_SESSION_SECONDS:
                        print(f"Sesion en OVERTIME: {session.external_sesion_id}")

                        session.overtime = True
                        db.session.flush()
                        binnacle = SessionBinnacle(**map_session_to_binnacle_data(session))
                        db.session.add(binnacle)
                        db.session.commit()

                        user = get_user_by_id(session.idUser)
                        if user.indNotificar:
                            try:
                                tz = timezone(session.timeZone)
                            except UnknownTimeZoneError:
                                tz = timezone("UTC")

                            local_start = session.startDate.astimezone(tz)
                            body = f"""
    <html>
    <body style="font-family: Arial, sans-serif; color: #333;">
      <div style="background-color: #fff3e0; padding: 10px; font-size: 20px; font-weight: bold; color: #ef6c00; border-left: 6px solid #ef6c00;">
        ⏰ SESIÓN EN OVERTIME DETECTADA
      </div>
    
      <p><strong>👤 Usuario:</strong> {user.name if user else 'Desconocido'} ({user.email if user else 'SIN CORREO'})</p>
      <p><strong>🔗 ID Externa:</strong> {session.external_sesion_id}</p>
      <p><strong>🕒 Inicio (Reloj usuario):</strong> {local_start.strftime('%Y-%m-%d %H:%M:%S %Z')}</p>
      <p><strong>🕒 Inicio (UTC):</strong> {session.startDate}</p>
      <p><strong>📁 Proyecto:</strong> {session.projectName}</p>
      <p><strong>📌 Tarea:</strong> {session.taskName}</p>
      <p><strong>📝 Descripción:</strong> {session.description}</p>
      <p><strong>⌛ Duración:</strong> {elapsed/3600:.2f} horas</p>
      <p><strong>⚠️ Estado:</strong> Marcado como OVERTIME</p>
    
      <div style="background-color: #fbe9e7; padding: 10px; border-left: 6px solid #d84315; color: #bf360c; margin-top: 20px;">
        La sesión sigue activa y ha superado el límite de 5 horas. Se ha registrado en la bitácora y enviado esta notificación.
      </div>
    </body>
    </html>
    """
                            send_webhook_email(
                                subject="Clockify - SESION en OVERTIME detectada",
                                data=body,
                                user_email=user.email if user else None
                            )

        except Exception as outer_e:
            with app.app_context():
                db.session.rollback()
                log_error_use_case(
                    endpoint="/monitor-open-sessions",
                    method="SYSTEM",
                    error=outer_e,
                    payload={"error": "general loop failure"},
                    response_code=500
                )

        time.sleep(60)