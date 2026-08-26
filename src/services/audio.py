import os

from gi.repository import GLib

from ..utils.formatters import collect_audio_files, track_display_name
from .settings import SettingsService

PRESET_TRACKS = [
    "Lo-fi Beats",
    "Rain Sounds",
    "White Noise",
    "Cafe Ambience",
    "Forest Sounds",
]


class AudioService:
    _instance = None
    _gst_ready = False
    _Gst = None

    @classmethod
    def get_default(cls):
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    @classmethod
    def _ensure_gst(cls):
        if cls._gst_ready:
            return cls._Gst is not None
        cls._gst_ready = True
        try:
            import gi

            gi.require_version("Gst", "1.0")
            from gi.repository import Gst

            Gst.init(None)
            cls._Gst = Gst
            return True
        except Exception:
            cls._Gst = None
            return False

    def __init__(self):
        self.settings = SettingsService.get_default()
        self.preset_tracks = list(PRESET_TRACKS)
        self.custom_tracks = []
        self.current_index = 0
        self.current_track_name = self.preset_tracks[0]
        self.custom_file_path = None
        self.is_playing = False
        self.volume = 0.6
        self.on_state_change_callbacks = []
        self.on_tracks_change_callbacks = []
        self._player = None
        self._bus_watch_id = None

        self._load_custom_tracks()
        self._restore_selection()
        self._init_player()
        self.settings.add_listener(self._on_settings_changed)

    def get_track_list(self) -> list:
        tracks = list(self.preset_tracks)
        for path in self.custom_tracks:
            tracks.append(track_display_name(path))
        return tracks

    def get_custom_tracks(self) -> list:
        return list(self.custom_tracks)

    def preset_count(self) -> int:
        return len(self.preset_tracks)

    def is_custom_index(self, index: int) -> bool:
        return index >= self.preset_count()

    def path_for_index(self, index: int):
        if not self.is_custom_index(index):
            return None
        custom_index = index - self.preset_count()
        if 0 <= custom_index < len(self.custom_tracks):
            return self.custom_tracks[custom_index]
        return None

    def add_paths(self, paths) -> int:
        new_files = collect_audio_files(paths)
        if not new_files:
            return 0

        existing = set(self.custom_tracks)
        added = 0
        for path in new_files:
            if path in existing:
                continue
            self.custom_tracks.append(path)
            existing.add(path)
            added += 1

        if added:
            self._persist_custom_tracks()
            self._notify_tracks_change()
        return added

    def remove_custom_track(self, path: str) -> bool:
        if path not in self.custom_tracks:
            return False

        was_current = self.custom_file_path == path
        self.custom_tracks = [p for p in self.custom_tracks if p != path]
        self._persist_custom_tracks()

        if was_current:
            playing = self.is_playing
            self.stop()
            self.select_track(0)
            if playing and self.custom_file_path is None:
                # Stay stopped after removing the active custom track.
                pass

        self._notify_tracks_change()
        self._notify_state_change()
        return True

    def clear_custom_tracks(self):
        if not self.custom_tracks:
            return
        playing = self.is_playing and self.custom_file_path
        self.custom_tracks = []
        self._persist_custom_tracks()
        if playing:
            self.stop()
            self.select_track(0)
        self._notify_tracks_change()
        self._notify_state_change()

    def select_track(self, index: int):
        tracks = self.get_track_list()
        if not tracks:
            return
        index = max(0, min(index, len(tracks) - 1))
        was_playing = self.is_playing

        if index < self.preset_count():
            self.custom_file_path = None
            self.current_index = index
            self.current_track_name = self.preset_tracks[index]
        else:
            path = self.path_for_index(index)
            if not path:
                return
            self.custom_file_path = path
            self.current_index = index
            self.current_track_name = track_display_name(path)

        self.settings.set_string("selected-track", self._selection_key())
        self._apply_uri()
        if was_playing:
            self._set_playing(True)
        self._notify_state_change()

    def select_preset_track(self, index: int):
        if 0 <= index < len(self.preset_tracks):
            self.select_track(index)

    def set_custom_file(self, file_path: str):
        """Legacy helper: add one file and select it."""
        if not file_path:
            return
        added_or_existing = collect_audio_files([file_path])
        if not added_or_existing:
            return
        target = added_or_existing[0]
        self.add_paths([target])
        try:
            index = self.preset_count() + self.custom_tracks.index(target)
        except ValueError:
            return
        self.select_track(index)

    def set_volume(self, volume: float):
        self.volume = max(0.0, min(1.0, volume))
        if self._player is not None:
            self._player.set_property("volume", self.volume)
        self._notify_state_change()

    def toggle(self):
        if self.is_playing:
            self.pause()
        else:
            self.play()

    def play(self):
        self._set_playing(True)
        self._notify_state_change()

    def pause(self):
        self._set_playing(False)
        self._notify_state_change()

    def stop(self):
        if self._player is not None and self._Gst is not None:
            self._player.set_state(self._Gst.State.NULL)
        if self.is_playing:
            self.is_playing = False
            self._notify_state_change()

    def _notify_state_change(self):
        for callback in list(self.on_state_change_callbacks):
            try:
                callback(self.is_playing, self.current_track_name, self.volume)
            except Exception:
                pass

    def _notify_tracks_change(self):
        for callback in list(self.on_tracks_change_callbacks):
            try:
                callback(self.get_track_list())
            except Exception:
                pass

    def _load_custom_tracks(self):
        stored = self.settings.get_strv("custom-tracks")
        self.custom_tracks = [path for path in stored if path and os.path.isfile(path)]

    def _persist_custom_tracks(self):
        self.settings.set_strv("custom-tracks", self.custom_tracks)

    def _selection_key(self) -> str:
        if self.custom_file_path:
            return f"custom:{self.custom_file_path}"
        return f"preset:{self.current_index}"

    def _restore_selection(self):
        key = self.settings.get_string("selected-track", "preset:0")
        if key.startswith("custom:"):
            path = key[7:]
            if path in self.custom_tracks:
                self.custom_file_path = path
                self.current_index = self.preset_count() + self.custom_tracks.index(
                    path
                )
                self.current_track_name = track_display_name(path)
                return
        if key.startswith("preset:"):
            try:
                index = int(key.split(":", 1)[1])
            except ValueError:
                index = 0
            if 0 <= index < self.preset_count():
                self.custom_file_path = None
                self.current_index = index
                self.current_track_name = self.preset_tracks[index]
                return
        self.custom_file_path = None
        self.current_index = 0
        self.current_track_name = self.preset_tracks[0]

    def _on_settings_changed(self, key):
        if key != "custom-tracks":
            return
        previous = list(self.custom_tracks)
        self._load_custom_tracks()
        if previous != self.custom_tracks:
            if (
                self.custom_file_path
                and self.custom_file_path not in self.custom_tracks
            ):
                self.stop()
                self.select_track(0)
            self._notify_tracks_change()

    def _init_player(self):
        if not self._ensure_gst():
            return
        Gst = self._Gst
        self._player = Gst.ElementFactory.make("playbin", "maldoro-player")
        if self._player is None:
            return
        self._player.set_property("volume", self.volume)
        bus = self._player.get_bus()
        bus.add_signal_watch()
        self._bus_watch_id = bus.connect("message", self._on_bus_message)
        self._apply_uri()

    def _apply_uri(self):
        if self._player is None or self._Gst is None:
            return
        Gst = self._Gst
        self._player.set_state(Gst.State.NULL)
        if self.custom_file_path and os.path.isfile(self.custom_file_path):
            uri = GLib.filename_to_uri(self.custom_file_path, None)
            self._player.set_property("uri", uri)

    def _set_playing(self, playing: bool):
        self.is_playing = playing
        if self._player is None:
            return
        Gst = self._Gst
        if playing:
            if self.custom_file_path:
                self._apply_uri()
                self._player.set_state(Gst.State.PLAYING)
            else:
                self._player.set_state(Gst.State.NULL)
        else:
            if self.custom_file_path:
                self._player.set_state(Gst.State.PAUSED)
            else:
                self._player.set_state(Gst.State.NULL)

    def _on_bus_message(self, _bus, message):
        Gst = self._Gst
        if Gst is None:
            return
        if message.type == Gst.MessageType.EOS:
            self._player.seek_simple(
                Gst.Format.TIME,
                Gst.SeekFlags.FLUSH | Gst.SeekFlags.KEY_UNIT,
                0,
            )
            self._player.set_state(Gst.State.PLAYING)
        elif message.type == Gst.MessageType.ERROR:
            self.is_playing = False
            self._player.set_state(Gst.State.NULL)
            self._notify_state_change()
