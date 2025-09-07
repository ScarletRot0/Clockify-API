import time
from datetime import datetime, timedelta, UTC
from threading import Event
from app.use_cases.send_periodic_reports import send_periodic_report
from app.extensions import db
from app.use_cases.manage_error_log import log_error_use_case

def start_report_scheduler(app):
    print("Iniciando scheduler de reportes semanales y mensuales", flush=True)
    stop_event = Event()

    def should_run_weekly(now):
        return now.weekday() == 5 and now.hour == 7 and now.minute == 0  # Sábado 7 AM UTC

    def should_run_monthly(now):
        return now.day == 1 and now.hour == 7 and now.minute == 0  # Primer día del mes 7 AM UTC

    while not stop_event.is_set():
        try:
            with app.app_context():
                now = datetime.now(UTC).replace(second=0, microsecond=0)

                if should_run_weekly(now):
                    last_saturday = (now - timedelta(days=7)).date()

                    print(
                        f"[REPORTE SEMANAL] Generando reporte desde: {last_saturday.strftime('%Y-%m-%d')} hasta {(last_saturday + timedelta(days=6)).strftime('%Y-%m-%d')}",
                        flush=True
                    )
                    send_periodic_report("weekly", start_date=last_saturday.strftime("%Y-%m-%d"))

                if should_run_monthly(now):
                    last_month = 12 if now.month == 1 else now.month - 1
                    year = now.year - 1 if now.month == 1 else now.year
                    print(f"[REPORTE MENSUAL] Generando reporte para el mes: {last_month}, año: {year}", flush=True)
                    send_periodic_report("monthly", month=last_month, year=year)

        except Exception as e:
            with app.app_context():
                db.session.rollback()
                log_error_use_case(
                    endpoint="/report-scheduler",
                    method="SYSTEM",
                    error=e,
                    payload={"message": "Error en el envio de reportes"},
                    response_code=500
                )

        time.sleep(60)