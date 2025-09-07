from app.extensions import db
from app.models.error_log import ErrorLog

def create_error_log(error_data: dict):
    try:
        error = ErrorLog(**error_data)
        db.session.add(error)
        db.session.commit()
        return {"message": "Error log saved successfully."}
    except Exception as e:
        db.session.rollback()
        return {"message": "Failed to save error log.", "details": str(e)}