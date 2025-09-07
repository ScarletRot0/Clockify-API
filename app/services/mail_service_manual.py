import smtplib
import time
import os
import base64
from email.message import EmailMessage
from flask import current_app
from app.use_cases.manage_error_log import log_error_use_case

MAX_RETRIES = int(os.getenv("EMAIL_MAX_RETRIES", 3))
RETRY_DELAY = int(os.getenv("EMAIL_RETRY_DELAY", 5))  # segundos

def send_webhook_email(subject, data, user_email=None, attachments=None, attempt=0):
    smtp_server = current_app.config["MAIL_SERVER"]
    smtp_port = current_app.config["MAIL_PORT"]
    username = current_app.config["MAIL_USERNAME"]
    password = current_app.config["MAIL_PASSWORD"]
    sender = current_app.config["MAIL_DEFAULT_SENDER"]
    main_recipient = current_app.config["MAIL_RECIPIENT"]

    additional_recipients_raw = current_app.config.get("MAIL_ADDITIONAL_RECIPIENTS", "")
    additional_recipients = [email.strip() for email in additional_recipients_raw.split(",") if email.strip()]
    recipients = [main_recipient] + additional_recipients

    if user_email and user_email != main_recipient:
        recipients.append(user_email)

    try:
        with smtplib.SMTP(smtp_server, smtp_port, timeout=10) as server:
            server.ehlo()
            server.starttls()
            server.ehlo()
            server.login(username, password)
            try:
                msg = EmailMessage()
                msg["Subject"] = subject
                msg["From"] = sender
                msg["To"] = ', '.join(recipients)
                msg.set_content("Este correo contiene contenido HTML. Por favor usa un cliente compatible.")
                msg.add_alternative(data, subtype='html', charset="utf-8")

                if attachments:
                    for att in attachments:
                        filename = att["filename"]
                        content_bytes = base64.b64decode(att["content_bytes"])  # Decode base64
                        mime_type = att["mime_type"]
                        maintype, subtype = mime_type.split("/", 1)
                        msg.add_attachment(content_bytes, maintype=maintype, subtype=subtype, filename=filename)

                server.send_message(msg)
                print(f"Correo enviado a {', '.join(recipients)}")
                return  # Éxito salir del bucle de reintento

            except smtplib.SMTPException as e:
                        print(f"Error al enviar a {', '.join(recipients)} (intento {attempt}): {str(e)}")
                        log_error_use_case(
                            endpoint="send_email",
                            method="POST",
                            error=e,
                            payload={"message": data, "recipient": ', '.join(recipients), "attempt": attempt, "subject": subject},
                            response_code=500
                        )
            raise e

    except Exception as e:
        print(f"Error al conectar con servidor SMTP: {str(e)}")
        log_error_use_case(
            endpoint="send_email",
            method="POST",
            error=e,
            payload={"message": data},
            response_code=500
        )
        raise e
