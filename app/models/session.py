from app.extensions import db
from datetime import datetime, timezone

class Session(db.Model):
    __tablename__ = 'sesiones'  # Casi la cago aquí

    idSesion = db.Column('idSesion', db.Integer, primary_key=True)
    description = db.Column('description', db.Text, nullable=False)
    external_sesion_id = db.Column('ExternalSesionId', db.String(50), unique=True, nullable=False)  # ID de Clockify
    idUser = db.Column('idUser', db.Integer, nullable=False)
    idProject = db.Column('idProject', db.String(64), nullable=False)
    projectName = db.Column('projectName', db.Text, nullable=False)

    idWorkspace = db.Column('idWorkspace', db.String(64), nullable=False)
    workspaceName = db.Column('workspaceName', db.Text, nullable=False)

    idTask = db.Column('idTask', db.String(64), nullable=False)
    taskName = db.Column('taskName', db.Text, nullable=False)

    startDate = db.Column('startDate', db.DateTime(timezone=True), nullable=False)
    endDate = db.Column('endDate', db.DateTime(timezone=True), nullable=True)
    duration = db.Column('duration', db.Interval, nullable=True)

    timeZone = db.Column('timeZone', db.Text, nullable=False)
    offsetStart = db.Column('offsetStart', db.Integer, nullable=False)
    offsetEnd = db.Column('offsetEnd', db.Integer, nullable=True)

    currentlyRunning = db.Column('currentlyRunning', db.Boolean, default=False)
    overtime = db.Column('overtime', db.Boolean, default=False)

    enable = db.Column('enable', db.Boolean, default=True)
    disableTime = db.Column('disableTime', db.DateTime(timezone=True), nullable=True)
    updatingQuantity = db.Column('updatingQuantity', db.Integer, default=0)
    #nuevo crud
    observation = db.Column('observation', db.String(500), nullable=True)
    status = db.Column('status', db.String(50), nullable=True)
    ValidStartDate = db.Column('ValidStartDate', db.DateTime(timezone=True), nullable=True)
    ValidEndDate = db.Column('ValidEndDate', db.DateTime(timezone=True), nullable=True)
    ValidDuration = db.Column('ValidDuration', db.Interval, nullable=True)
