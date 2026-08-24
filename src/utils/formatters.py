def format_time(seconds: int) -> str:
    seconds = max(0, seconds)
    minutes, secs = divmod(seconds, 60)
    return f"{minutes:02d}:{secs:02d}"


def format_focus_time(total_seconds: int) -> str:
    total_minutes = max(0, total_seconds) // 60
    if total_minutes < 60:
        return f"{total_minutes}m"
    hours, minutes = divmod(total_minutes, 60)
    return f"{hours}h {minutes}m"


def format_sessions(count: int) -> str:
    count = max(0, count)
    suffix = "session" if count == 1 else "sessions"
    return f"{count} {suffix}"


def track_display_name(file_path: str) -> str:
    return os.path.basename(file_path)
