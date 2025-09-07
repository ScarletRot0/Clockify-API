from app.extensions import db
from app.models.session_binnacle import SessionBinnacle
from app.models.user import User  # necesario para buscar por email
from sqlalchemy import func, and_

def create_session_binnacle(data):
    binnacle = SessionBinnacle(**data)
    db.session.add(binnacle)
    db.session.commit()
    return binnacle


def list_all_session_binnacles():
    return SessionBinnacle.query.all()


def get_session_binnacle_by_id(id_binnacle):
    return SessionBinnacle.query.get(id_binnacle)


def get_binnacles_by_session_id(id_sesion):
    return SessionBinnacle.query.filter_by(idSesion=id_sesion).all()


def get_binnacles_by_external_session_id(external_sesion_id):
    return SessionBinnacle.query.filter_by(external_sesion_id=external_sesion_id).all()


def get_binnacles_by_project_name(project_name):
    return SessionBinnacle.query.filter(
        func.lower(SessionBinnacle.projectName) == project_name.lower()
    ).all()


def get_binnacles_by_start_date(start_date):
    return SessionBinnacle.query.filter(
        func.date(SessionBinnacle.startDate) == start_date
    ).all()


def get_binnacles_by_user_email(email):
    return (
        db.session.query(SessionBinnacle)
        .join(User, SessionBinnacle.idUser == User.id)
        .filter(func.lower(User.email) == email.lower())
        .all()
    )

def get_binnacles_by_start_date_range(from_date, to_date=None):
    query = SessionBinnacle.query
    if to_date:
        return query.filter(
            and_(
                func.date(SessionBinnacle.startDate) >= from_date,
                func.date(SessionBinnacle.startDate) <= to_date
            )
        ).all()
    else:
        return query.filter(func.date(SessionBinnacle.startDate) >= from_date).all()