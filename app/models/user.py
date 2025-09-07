from app.extensions import db
class User(db.Model):
    __tablename__ = 'users'

    id = db.Column('idUser', db.Integer, primary_key=True)  # Clave primaria autoincremental
    external_user_id = db.Column('ExternalUserId', db.String(50), unique=True, nullable=False)  # ID de Clockify
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=False, nullable=True)
    hours_per_month = db.Column('hoursPerMonth', db.Integer, nullable=True)
    enable = db.Column(db.Boolean, default=True)
    disabled_time = db.Column('disableTime', db.DateTime(timezone=True), nullable=True)
    indNotificar = db.Column('indNotificar', db.Boolean, default=True)