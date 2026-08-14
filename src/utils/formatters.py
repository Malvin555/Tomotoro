# Helper formatting utilities

def format_time(seconds: int) -> str:
    """Format total seconds into MM:SS display format."""
    seconds = max(0, seconds)
    minutes, secs = divmod(seconds, 60)
    return f"{minutes:02d}:{secs:02d}"


def format_focus_time(total_seconds: int) -> str:
    """Format total focus time into human readable duration."""
    total_minutes = max(0, total_seconds) // 60
    if total_minutes < 60:
        return f"{total_minutes}m"
    hours, minutes = divmod(total_minutes, 60)
    return f"{hours}h {minutes}m"


def format_sessions(count: int) -> str:
    """Format completed session count."""
    count = max(0, count)
    suffix = "session" if count == 1 else "sessions"
    return f"{count} {suffix}"
