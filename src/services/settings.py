from gi.repository import Gio

SCHEMA_ID = "org.tomotoro.fyvin"


class SettingsService:
    _instance = None

    @classmethod
    def get_default(cls):
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def __init__(self):
        self.settings = None
        self._listeners = []
        self._fallback = {
            "focus-length": 25,
            "break-length": 5,
            "auto-start-breaks": False,
            "auto-start-focus": False,
            "sound-enabled": True,
            "custom-tracks": [],
            "selected-track": "preset:0",
            "play-music-with-timer": False,
        }
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
        if callback not in self._listeners:
            self._listeners.append(callback)

    def remove_listener(self, callback):
        if callback in self._listeners:
            self._listeners.remove(callback)

    def get_int(self, key: str, default: int) -> int:
        if self.settings:
            try:
                return self.settings.get_int(key)
            except Exception:
                pass
        return self._fallback.get(key, default)

    def get_boolean(self, key: str, default: bool) -> bool:
        if self.settings:
            try:
                return self.settings.get_boolean(key)
            except Exception:
                pass
        return self._fallback.get(key, default)

    def get_string(self, key: str, default: str = "") -> str:
        if self.settings:
            try:
                return self.settings.get_string(key)
            except Exception:
                pass
        return self._fallback.get(key, default)

    def set_string(self, key: str, value: str):
        if self.settings:
            try:
                self.settings.set_string(key, value)
                return
            except Exception:
                pass
        self._fallback[key] = value
        self._on_changed(None, key)

    def get_strv(self, key: str) -> list:
        if self.settings:
            try:
                return list(self.settings.get_strv(key))
            except Exception:
                pass
        return list(self._fallback.get(key, []))

    def set_strv(self, key: str, values: list):
        values = list(values)
        if self.settings:
            try:
                self.settings.set_strv(key, values)
                return
            except Exception:
                pass
        self._fallback[key] = values
        self._on_changed(None, key)

    def get_focus_length(self) -> int:
        return self.get_int("focus-length", 25)

    def get_break_length(self) -> int:
        return self.get_int("break-length", 5)

    def is_auto_start_breaks(self) -> bool:
        return self.get_boolean("auto-start-breaks", False)

    def is_auto_start_focus(self) -> bool:
        return self.get_boolean("auto-start-focus", False)

    def is_sound_enabled(self) -> bool:
        return self.get_boolean("sound-enabled", True)

    def is_play_music_with_timer(self) -> bool:
        return self.get_boolean("play-music-with-timer", False)

    def bind(
        self,
        key: str,
        object_instance,
        property_name: str,
        flags=Gio.SettingsBindFlags.DEFAULT,
    ):
        if self.settings:
            try:
                self.settings.bind(key, object_instance, property_name, flags)
            except Exception:
                pass
