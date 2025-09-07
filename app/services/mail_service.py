from flask_mail import Message
from flask import current_app
from app.extensions import mail

def send_webhook_email(subject, data):
    recipient = current_app.config["MAIL_RECIPIENT"]
    msg = Message(
        subject=subject,
        recipients=[recipient],
        body=data
    )
    mail.send(msg)
