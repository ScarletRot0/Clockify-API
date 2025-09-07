from datetime import timedelta
def format_duration(duration):
    if not duration:
        return 0
    total_seconds = duration.total_seconds()
    return round(total_seconds / 3600, 2)

def format_duration_as_hms(duration: timedelta) -> str:
    if not duration:
        return None
    total_seconds = int(duration.total_seconds())
    hours, remainder = divmod(total_seconds, 3600)
    minutes, seconds = divmod(remainder, 60)
    return f"{hours:02}:{minutes:02}:{seconds:02}"