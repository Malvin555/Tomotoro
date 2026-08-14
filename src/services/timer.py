# Timer business logic service
from gi.repository import GLib
from .settings import SettingsService

MODE_FOCUS = "focus"
MODE_SHORT = "short"
MODE_LONG = "long"

MODE_TITLES = {
    MODE_FOCUS: "Focus",
    MODE_SHORT: "Short Break",
    MODE_LONG: "Long Break",
}


class TimerService:
    """Encapsulates the Pomodoro timer countdown and state management."""

    def __init__(self):
        self.settings = SettingsService.get_default()
        self.mode = MODE_FOCUS
        self.durations = {
            MODE_FOCUS: 25 * 60,
            MODE_SHORT: 5 * 60,
            MODE_LONG: 15 * 60,
        }
        self._load_durations()
        self.total_seconds = self.durations[self.mode]
        self.seconds_left = self.total_seconds
        self.running = False
        self.timer_source_id = None
        self.sessions_completed = 0
        self.focus_seconds_total = 0

        self.on_tick_callbacks = []
        self.on_complete_callbacks = []
        self.on_state_change_callbacks = []

        self.settings.add_listener(self._on_settings_changed)

    def _load_durations(self):
        self.durations[MODE_FOCUS] = self.settings.get_focus_length() * 60
        self.durations[MODE_SHORT] = self.settings.get_short_break_length() * 60
        self.durations[MODE_LONG] = self.settings.get_long_break_length() * 60

    def _on_settings_changed(self, key):
        self._load_durations()
        if not self.running:
            self.total_seconds = self.durations[self.mode]
            self.seconds_left = self.total_seconds
            self._notify_state_change()

    def set_mode(self, mode: str):
        if mode not in self.durations:
            return
        self.stop()
        self.mode = mode
        self.total_seconds = self.durations[mode]
        self.seconds_left = self.total_seconds
        self._notify_state_change()

    def start(self):
        if self.running:
            return
        self.running = True
        if self.timer_source_id is None:
            self.timer_source_id = GLib.timeout_add(1000, self._tick)
        self._notify_state_change()

    def stop(self):
        self.running = False
        if self.timer_source_id is not None:
            GLib.source_remove(self.timer_source_id)
            self.timer_source_id = None
        self._notify_state_change()

    def toggle(self):
        if self.running:
            self.stop()
        else:
            self.start()

    def reset(self):
        self.stop()
        self.seconds_left = self.total_seconds
        self._notify_state_change()

    def skip(self):
        self._on_complete()

    def _tick(self):
        if self.seconds_left <= 0:
            self._on_complete()
            return False

        self.seconds_left -= 1
        if self.mode == MODE_FOCUS:
            self.focus_seconds_total += 1

        fraction = 1.0 - (self.seconds_left / self.total_seconds) if self.total_seconds > 0 else 0.0
        for callback in self.on_tick_callbacks:
            try:
                callback(self.seconds_left, self.total_seconds, max(0.0, min(1.0, fraction)))
            except Exception:
                pass

        return True

    def _on_complete(self):
        self.stop()
        if self.mode == MODE_FOCUS:
            self.sessions_completed += 1

        for callback in self.on_complete_callbacks:
            try:
                callback(self.mode, self.sessions_completed)
            except Exception:
                pass

        self._notify_state_change()

    def _notify_state_change(self):
        fraction = 1.0 - (self.seconds_left / self.total_seconds) if self.total_seconds > 0 else 0.0
        for callback in self.on_state_change_callbacks:
            try:
                callback(self.mode, self.running, self.seconds_left, self.total_seconds, max(0.0, min(1.0, fraction)))
            except Exception:
                pass
