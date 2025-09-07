from app.extensions import db
from app.models.user import User
from datetime import datetime, UTC
from app.models.session import Session
from sqlalchemy import func, and_

def get_users_with_session_on(date):
    return (
        db.session.query(User)
        .join(Session, User.id == Session.idUser)
        .filter(func.date(Session.startDate) == date)
        .distinct()
        .all()
    )

def get_users_with_session_between(from_date, to_date=None):
    query = (
        db.session.query(User)
        .join(Session, User.id == Session.idUser)
    )

    if to_date:
        query = query.filter(
            and_(
                func.date(Session.startDate) >= from_date,
                func.date(Session.startDate) <= to_date
            )
        )
    else:
        query = query.filter(func.date(Session.startDate) >= from_date)

    return query.distinct().all()

def get_all_users():
    return User.query.all()


def get_user_by_id(user_id):
    return User.query.get(user_id)


def get_user_by_email(user_email):
    return User.query.filter_by(email=user_email).first()


def get_user_by_external_id(external_id):
    return User.query.filter_by(external_user_id=external_id).first()


def create_user(data):
    user = User(
        external_user_id=data.get("ExternalUserId"),
        name=data.get("name"),
        email=data.get("email", ""),
        hours_per_month=data.get("hoursPerMonth", 0),
        enable=data.get("enable", True),
        disabled_time=data.get("disabledTime"),
        notify=data.get("notify", True)
    )
    db.session.add(user)
    db.session.commit()
    return user


def update_user(user_id, data):
    user = User.query.get(user_id)
    if not user:
        return None

    user.name = data.get("name", user.name)
    user.email = data.get("email", user.email)
    user.hours_per_month = data.get("hoursPerMonth", user.hours_per_month)
    user.enable = data.get("enable", user.enable)
    user.external_user_id = data.get("ExternalUserId", user.external_user_id)
    user.notify = data.get("notify", user.notify)

    if user.enable is False:
        user.disabled_time = data.get("disabledTime", datetime.now(UTC))
    else:
        user.disabled_time = None

    db.session.commit()
    return user

def update_user_by_external_id(external_id, data):
    user = User.query.filter_by(external_user_id=external_id).first()
    if not user:
        return None

    user.name = data.get('name', user.name)
    user.email = data.get('email', user.email)
    user.hours_per_month = data.get('hoursPerMonth', user.hours_per_month)
    user.enable = data.get('enable', user.enable)
    user.notify = data.get('notify', user.notify)

    if user.enable is False:
        user.disabled_time = data.get('disabledTime', datetime.now(UTC))
    else:
        user.disabled_time = None

    db.session.commit()
    return user

def delete_user(user_id):
    user = User.query.get(user_id)
    if not user:
        return False

    db.session.delete(user)
    db.session.commit()
    return True

def delete_user_by_external_id(external_id):
    user = User.query.filter_by(external_user_id=external_id).first()
    if not user:
        return False

    db.session.delete(user)
    db.session.commit()
    return True