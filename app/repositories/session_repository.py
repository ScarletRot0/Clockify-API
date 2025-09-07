from app.extensions import db
from app.models.session import Session
from app.models.user import User
from sqlalchemy import func, and_

def get_sessions_by_start_date(date):
    return Session.query.filter(func.date(Session.startDate) == date).all()

def get_sessions_by_start_date_range(from_date, to_date=None):
    query = Session.query
    if to_date:
        return query.filter(
            and_(
                func.date(Session.startDate) >= from_date,
                func.date(Session.startDate) <= to_date
            )
        ).all()
    else:
        return query.filter(func.date(Session.startDate) >= from_date).all()
def list_sessions():
    return Session.query.all()

def get_session_by_id(session_id):
    return Session.query.get(session_id)

def get_sessions_by_user_id(user_id):
    return Session.query.filter_by(idUser=user_id).all()

def get_sessions_by_user_email(email):
    return (
        db.session.query(Session)
        .join(User, Session.idUser == User.id)
        .filter(User.email == email)
        .all()
    )

def create_session(data):
    session = Session(**data)
    db.session.add(session)
    db.session.commit()
    return session

def update_session(session_id, data):
    session = Session.query.get(session_id)
    if not session:
        return None

    for key, value in data.items():
        if hasattr(session, key):
            setattr(session, key, value)

    db.session.commit()
    return session

def delete_session(session_id):
    session = Session.query.get(session_id)
    if not session:
        return False

    db.session.delete(session)
    db.session.commit()
    return True
