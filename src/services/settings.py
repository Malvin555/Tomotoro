# Settings management service
from gi.repository import Gio

SCHEMA_ID = "org.maldoro.fyvin"


class SettingsService:
    """Manages application settings and schema bindings with fallback support."""

    _instance = None

    @classmethod
    def get_default(cls):
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def __init__(self):
        self.settings = None
        self._listeners = []
        self._init_settings()

    def _init_settings(self):
        try:
            source = Gio.SettingsSchemaSource.get_default()
            if source and source.lookup(SCHEMA_ID, True):
                self.settings = Gio.Settings.new(SCHEMA_ID)
                self.settings.connect("changed", self._on_changed)
        except Exception:
            self.settings = None

    def _on_changed(self, settings, key):
        for callback in self._listeners:
            try:
                callback(key)
            except Exception:
                pass

    def add_listener(self, callback):
        """Register a callback for settings changes."""
        if callback not in self._listeners:
            self._listeners.append(callback)

    def remove_listener(self, callback):
        """Unregister a settings change callback."""
        if callback in self._listeners:
            self._listeners.remove(callback)

    def get_int(self, key: str, default: int) -> int:
        if self.settings:
            try:
                return self.settings.get_int(key)
            except Exception:
                pass
        return default

    def get_boolean(self, key: str, default: bool) -> bool:
        if self.settings:
            try:
                return self.settings.get_boolean(key)
            except Exception:
                pass
        return default

    def get_focus_length(self) -> int:
        return self.get_int("focus-length", 25)

    def get_short_break_length(self) -> int:
        return self.get_int("short-break-length", 5)

    def get_long_break_length(self) -> int:
        return self.get_int("long-break-length", 15)

    def get_sessions_before_long_break(self) -> int:
        return self.get_int("sessions-until-long-break", 4)

    def is_sound_enabled(self) -> bool:
        return self.get_boolean("sound-enabled", True)

    def bind(self, key: str, object_instance, property_name: str, flags=Gio.SettingsBindFlags.DEFAULT):
        """Bind a setting key to a widget property."""
        if self.settings:
            try:
                self.settings.bind(key, object_instance, property_name, flags)
            except Exception:
                pass
