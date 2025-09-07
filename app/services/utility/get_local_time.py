from datetime import timedelta
def get_local_time(date, offset_seconds):
    if date is None or offset_seconds is None:
        return None
    return date + timedelta(seconds=offset_seconds)