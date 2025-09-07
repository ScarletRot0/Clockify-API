import time
import os
from datetime import datetime, UTC
from app.extensions import db
from app.models.email_queue import EmailQueue
from app.services.mail_service_manual import send_webhook_email
from app.use_cases.manage_error_log import log_error_use_case
from threading import Event

MAX_RETRIES = int(os.getenv("EMAIL_MAX_RETRIES", 3))
PROCESS_INTERVAL = int(os.getenv("EMAIL_PROCESS_INTERVAL", 5))  # segundos

def start_email_sender(app):
    print("Iniciando daemon de desencolamiento de correos", flush=True)
    stop_event = Event()

    while not stop_event.is_set():
        try:
            with app.app_context():
                emails = EmailQueue.query.filter_by(status=0).order_by(EmailQueue.createdAt).limit(5).all()

                for email in emails:
                    try:
                        send_webhook_email(
                            subject=email.subject,
                            data=email.body,
                            user_email=email.toAddress,
                            attachments=email.attachments,
                            attempt=email.retries
                        )
                        email.status = 1
                        email.sentAt = datetime.now(UTC)
                    except Exception as e:
                        email.retries += 1
                        if email.retries >= MAX_RETRIES:
                            email.status = 2  # fallido permanente
                        log_error_use_case(
                            endpoint="/email-daemon",
                            method="SYSTEM",
                            error=e,
                            payload={"emailId": email.idEncolado, "body": email.body, "subject": email.subject, "retries": email.retries},
                            response_code=500
                        )
                    finally:
                        db.session.commit()

        except Exception as outer_e:
            with app.app_context():
                db.session.rollback()
                log_error_use_case(
                    endpoint="/email-daemon",
                    method="SYSTEM",
                    error=outer_e,
                    payload={"error": "Error general del loop"},
                    response_code=500
                )

        time.sleep(PROCESS_INTERVAL)
