from gi.repository import Gtk

from ..constant import MODE_BREAK, MODE_FOCUS

MODE_LOCK_TOOLTIP = "Pause the timer before changing mode"


class ModeSwitcher:
    def __init__(
        self,
        focus_toggle: Gtk.ToggleButton,
        break_toggle: Gtk.ToggleButton,
        on_mode_chosen,
    ):
        self.focus = focus_toggle
        self.break_mode = break_toggle
        self._on_mode_chosen = on_mode_chosen
        self._locked = False

        self.focus.connect("toggled", self._on_toggled, MODE_FOCUS)
        self.break_mode.connect("toggled", self._on_toggled, MODE_BREAK)

    def _buttons(self):
        return (
            self.focus,
            self.break_mode,
        )

    def sync(self, mode: str):
        self.focus.set_active(mode == MODE_FOCUS)
        self.break_mode.set_active(mode == MODE_BREAK)

    def set_locked(self, locked: bool):
        self._locked = bool(locked)

        for button in self._buttons():
            button.set_sensitive(not self._locked)

        if self._locked:
            self.focus.set_tooltip_text(MODE_LOCK_TOOLTIP)
            self.break_mode.set_tooltip_text(MODE_LOCK_TOOLTIP)
        else:
            self.focus.set_tooltip_text(None)
            self.break_mode.set_tooltip_text(None)

    def _on_toggled(self, button, mode):
        if self._locked:
            self.sync(MODE_FOCUS if self.focus.get_active() else MODE_BREAK)
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
        enabled = self.switch.get_active()

        # The music switch itself is always available
        self.switch.set_sensitive(True)

        # All music controls depend on the music switch
        self.controls.set_sensitive(enabled)
        self.track_dropdown.set_sensitive(enabled)

        # Turning music off pauses playback
        if not enabled and self.audio.is_playing:
            self.audio.pause()
            is_playing = False

        # Timer stopping also pauses playback
        if not running and self.audio.is_playing:
            self.audio.pause()
            is_playing = False

        playing = running and enabled and is_playing

        self.title_marquee.set_active(playing)
        self.track_dropdown.set_marquee_active(playing)
