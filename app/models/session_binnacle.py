from app.extensions import db
from datetime import datetime, UTC


class SessionBinnacle(db.Model):
    __tablename__ = 'sesiones_binnacle'

    idSesionBinnacle = db.Column(db.Integer, primary_key=True)
    external_sesion_id = db.Column('ExternalSesionId', db.String(50), unique=True, nullable=False)  # ID de Clockify
    idSesion = db.Column(db.Integer, nullable=False)
    description = db.Column(db.Text, nullable=False)
    idUser = db.Column(db.Integer, nullable=False)
    idProject = db.Column(db.String(50), nullable=False)
    projectName = db.Column(db.Text, nullable=False)
    idWorkspace = db.Column(db.String(50), nullable=False)
    workspaceName = db.Column(db.Text, nullable=False)
    idTask = db.Column(db.String(50), nullable=False)
    taskName = db.Column(db.Text, nullable=False)
    startDate = db.Column(db.DateTime(timezone=True), nullable=False)
    endDate = db.Column(db.DateTime(timezone=True), nullable=True)
    createdAt = db.Column(db.DateTime(timezone=True), default=datetime.now(UTC))
    modifiedAt = db.Column(db.DateTime(timezone=True), default=datetime.now(UTC))
    duration = db.Column(db.Interval, nullable=True)
    timeZone = db.Column(db.Text, nullable=False)
    offsetStart = db.Column(db.Integer, nullable=False)
    offsetEnd = db.Column(db.Integer, nullable=True)
    updatingQuantity = db.Column(db.Integer, default=0)
    enable = db.Column(db.Boolean, default=True)
    disableTime = db.Column(db.DateTime(timezone=True), nullable=True)
    #nuevo crud
    observation = db.Column('observation', db.String(500), nullable=True)
    status = db.Column('status', db.String(50), nullable=True)
    ValidStartDate = db.Column('ValidStartDate', db.DateTime(timezone=True), nullable=True)
    ValidEndDate = db.Column('ValidEndDate', db.DateTime(timezone=True), nullable=True)
    ValidDuration = db.Column('ValidDuration', db.Interval, nullable=True)
