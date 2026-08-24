from datetime import date, timedelta

from .settings import SettingsService
from .timer import MODE_FOCUS


class AnalyticsService:
    _instance = None

    @classmethod
    def get_default(cls):
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def __init__(self):
        self.settings = SettingsService.get_default()
        self.total_sessions = 0
        self.total_focus_minutes = 0
        self.daily_focus_minutes = {}
        self.track_play_counts = {}
        self._was_playing = False
        self.on_change_callbacks = []

    def record_session(self, mode: str, sessions_completed: int):
        if mode != MODE_FOCUS:
            return
        minutes = self.settings.get_focus_length()
        self.total_sessions = sessions_completed
        self.total_focus_minutes += minutes

        today = date.today().isoformat()
        self.daily_focus_minutes[today] = (
            self.daily_focus_minutes.get(today, 0) + minutes
        )
        self._notify()

    def record_audio_state(
        self, is_playing: bool, current_track_name: str, volume: float
    ):
        if is_playing and not self._was_playing:
            self.track_play_counts[current_track_name] = (
                self.track_play_counts.get(current_track_name, 0) + 1
            )
            self._notify()
        self._was_playing = is_playing

    def get_last_7_days(self) -> list:
        result = []
        for offset in range(6, -1, -1):
            day = date.today() - timedelta(days=offset)
            label = day.strftime("%a")[0]
            minutes = self.daily_focus_minutes.get(day.isoformat(), 0)
            result.append((label, minutes))
        return result

    def get_most_played_track(self):
        if not self.track_play_counts:
            return None, 0
        name = max(self.track_play_counts, key=self.track_play_counts.get)
        return name, self.track_play_counts[name]

    def get_current_streak(self) -> int:
        streak = 0
        day = date.today()
        while self.daily_focus_minutes.get(day.isoformat(), 0) > 0:
            streak += 1
            day -= timedelta(days=1)
        return streak

    def get_total_focus_hours_minutes(self):
        return divmod(self.total_focus_minutes, 60)

    def _notify(self):
        for callback in self.on_change_callbacks:
            try:
                callback()
            except Exception:
                pass
