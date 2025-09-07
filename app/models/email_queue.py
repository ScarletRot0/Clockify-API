from app.extensions import db
from datetime import datetime, UTC
from sqlalchemy.dialects.postgresql import JSONB

class EmailQueue(db.Model):
    __tablename__ = "email_queue"

    idEncolado = db.Column("idEncolado", db.Integer, primary_key=True)
    toAddress = db.Column("toAddress", db.Text, nullable=False)
    subject = db.Column("subject", db.Text, nullable=False)
    body = db.Column("body", db.Text, nullable=False)
    status = db.Column("status", db.Integer, nullable=False, default=0)  # 0=queued, 1=sent, 2=failed
    retries = db.Column("retries", db.Integer, nullable=False, default=0)
    sentAt = db.Column("sentAt", db.DateTime(timezone=True), nullable=True)
    createdAt = db.Column("createdAt", db.DateTime(timezone=True), default=datetime.now(UTC))
    attachments = db.Column("attachments", JSONB, nullable=True)