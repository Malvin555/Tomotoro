import os

from ..utils.formatters import track_display_name

PRESET_TRACKS = [
    "Lo-fi Beats",
    "Rain Sounds",
    "White Noise",
    "Cafe Ambience",
    "Forest Sounds",
]


class AudioService:
    def __init__(self):
        self.preset_tracks = list(PRESET_TRACKS)
        self.custom_file_path = None
        self.current_track_name = self.preset_tracks[0]
        self.is_playing = False
        self.volume = 0.6
        self.on_state_change_callbacks = []

    def get_track_list(self) -> list:
        tracks = list(self.preset_tracks)
        if self.custom_file_path:
            tracks.append(f"📁 {track_display_name(self.custom_file_path)}")
        return tracks

    def select_preset_track(self, index: int):
        if 0 <= index < len(self.preset_tracks):
            self.custom_file_path = None
            self.current_track_name = self.preset_tracks[index]
            self._notify_state_change()

    def set_custom_file(self, file_path: str):
        if file_path and os.path.exists(file_path):
            self.custom_file_path = file_path
            self.current_track_name = track_display_name(file_path)
            self._notify_state_change()

    def set_volume(self, volume: float):
        self.volume = max(0.0, min(1.0, volume))
        self._notify_state_change()

    def toggle(self):
        self.is_playing = not self.is_playing
        self._notify_state_change()

    def stop(self):
        if self.is_playing:
            self.is_playing = False
            self._notify_state_change()

    def _notify_state_change(self):
        for callback in self.on_state_change_callbacks:
            try:
                callback(self.is_playing, self.current_track_name, self.volume)
            except Exception:
                pass
