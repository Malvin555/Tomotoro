import os

SUPPORTED_AUDIO_EXTENSIONS = (
    ".mp3",
    ".ogg",
    ".oga",
    ".opus",
    ".flac",
    ".wav",
    ".m4a",
    ".aac",
    ".wma",
    ".alac",
    ".aiff",
    ".ape",
    ".webm",
)


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
    name = os.path.basename(file_path or "")
    stem, _ext = os.path.splitext(name)
    clean = stem.replace("_", " ").replace("-", " ").strip()
    return clean or name or "Unknown track"


def is_supported_audio(path: str) -> bool:
    if not path or not os.path.isfile(path):
        return False
    return os.path.splitext(path)[1].lower() in SUPPORTED_AUDIO_EXTENSIONS


def collect_audio_files(paths) -> list:
    found = []
    seen = set()

    for path in paths:
        if not path:
            continue
        if os.path.isfile(path):
            if is_supported_audio(path):
                resolved = os.path.abspath(path)
                if resolved not in seen:
                    seen.add(resolved)
                    found.append(resolved)
        elif os.path.isdir(path):
            for root, _, files in os.walk(path):
                for name in sorted(files):
                    full = os.path.join(root, name)
                    if is_supported_audio(full):
                        resolved = os.path.abspath(full)
                        if resolved not in seen:
                            seen.add(resolved)
                            found.append(resolved)

    return found
