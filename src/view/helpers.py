from gi.repository import Gtk

from ..constant import MODE_FOCUS, MODE_LONG, MODE_SHORT

MODE_LOCK_TOOLTIP = ()


class ModeSwitcher:
    def __init__(
        self,
        focus_toggle: Gtk.ToggleButton,
        short_toggle: Gtk.ToggleButton,
        long_toggle: Gtk.ToggleButton,
        on_mode_chosen,
    ):
        self.focus = focus_toggle
        self.short = short_toggle
        self.long = long_toggle
        self._on_mode_chosen = on_mode_chosen
        self._locked = False

        self.focus.connect("toggled", self._on_toggled, MODE_FOCUS)
        self.short.connect("toggled", self._on_toggled, MODE_SHORT)
        self.long.connect("toggled", self._on_toggled, MODE_LONG)

    def _buttons(self):
        return (self.focus, self.short, self.long)

    def sync(self, mode: str):
        self.focus.set_active(mode == MODE_FOCUS)
        self.short.set_active(mode == MODE_SHORT)
        self.long.set_active(mode == MODE_LONG)

    def set_locked(self, locked: bool):
        self._locked = bool(locked)
        tooltip = MODE_LOCK_TOOLTIP if self._locked else None
        for button in self._buttons():
            button.set_sensitive(not self._locked)
            button.set_tooltip_text(tooltip)

    def _on_toggled(self, button, mode):
        if self._locked:
            return
        if button.get_active():
            self._on_mode_chosen(mode)


class MusicSessionGate:
    def __init__(
        self,
        music_switch: Gtk.Switch,
        controls_box: Gtk.Widget,
        title_marquee,
        track_dropdown,
        audio_service,
    ):
        self.switch = music_switch
        self.controls = controls_box
        self.title_marquee = title_marquee
        self.track_dropdown = track_dropdown
        self.audio = audio_service

    def refresh(self, running: bool, is_playing: bool):
        self.controls.set_sensitive(running)
        self.switch.set_sensitive(running)

        if not running and self.audio.is_playing:
            self.audio.stop()
            is_playing = False

        playing = running and is_playing
        self.title_marquee.set_active(playing)
        self.track_dropdown.set_marquee_active(playing)
