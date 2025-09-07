from app.extensions import db
from datetime import datetime, UTC


class ErrorLog(db.Model):
    __tablename__ = 'error_logs'

    idErrorLog = db.Column(db.Integer, primary_key=True)
    endpoint = db.Column(db.Text, nullable=False)
    method = db.Column(db.Text, nullable=False)
    errorMessage = db.Column(db.Text, nullable=False)
    stackTrace = db.Column(db.Text, nullable=True)
    payload = db.Column(db.JSON, nullable=True)
    responseCode = db.Column(db.Integer, nullable=False)
    createdAt = db.Column(db.DateTime(timezone=True), default=datetime.now(UTC))
    idUser = db.Column(db.Integer, nullable=True)
    enable = db.Column(db.Boolean, default=True)
    disableTime = db.Column(db.DateTime(timezone=True), nullable=True)
    externalUserId = db.Column('ExternalUserId', db.String(50), nullable=True)
