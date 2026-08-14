# Pomodoro view controller
from gi.repository import Gtk, Adw, Gdk, Gio

from ..services.timer import TimerService, MODE_FOCUS, MODE_SHORT, MODE_LONG, MODE_TITLES
from ..services.audio import AudioService
from ..services.settings import SettingsService
from ..utils.formatters import format_time, format_focus_time, format_sessions


@Gtk.Template(resource_path="/org/maldoro/fyvin/pomodoro.ui")
class PomodoroView(Gtk.Box):
    """View controller for the Pomodoro page."""

    __gtype_name__ = "PomodoroView"

    toast_overlay = Gtk.Template.Child()
    mode_focus_toggle = Gtk.Template.Child()
    mode_short_toggle = Gtk.Template.Child()
    mode_long_toggle = Gtk.Template.Child()
    status_label = Gtk.Template.Child()
    timer_label = Gtk.Template.Child()
    progress_bar = Gtk.Template.Child()
    start_button = Gtk.Template.Child()
    reset_button = Gtk.Template.Child()
    skip_button = Gtk.Template.Child()
    music_switch = Gtk.Template.Child()
    music_controls_box = Gtk.Template.Child()
    track_dropdown = Gtk.Template.Child()
    music_file_button = Gtk.Template.Child()
    music_play_button = Gtk.Template.Child()
    volume_scale = Gtk.Template.Child()
    sessions_today_value = Gtk.Template.Child()
    focus_time_value = Gtk.Template.Child()

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        self.timer_service = TimerService()
        self.audio_service = AudioService()
        self.settings_service = SettingsService.get_default()

        self._setup_signals()
        self._setup_audio_tracks()
        self._sync_view()

    # Setup & initialization 
    def _setup_signals(self):
        # Timer service callbacks
        self.timer_service.on_tick_callbacks.append(self._on_timer_tick)
        self.timer_service.on_complete_callbacks.append(self._on_timer_complete)
        self.timer_service.on_state_change_callbacks.append(self._on_timer_state_changed)

        # Audio service callbacks
        self.audio_service.on_state_change_callbacks.append(self._on_audio_state_changed)

        # UI actions
        self.mode_focus_toggle.connect("toggled", self._on_mode_button_toggled, MODE_FOCUS)
        self.mode_short_toggle.connect("toggled", self._on_mode_button_toggled, MODE_SHORT)
        self.mode_long_toggle.connect("toggled", self._on_mode_button_toggled, MODE_LONG)

        self.start_button.connect("clicked", lambda *_: self.timer_service.toggle())
        self.reset_button.connect("clicked", lambda *_: self.timer_service.reset())
        self.skip_button.connect("clicked", lambda *_: self.timer_service.skip())

        self.music_switch.connect("notify::active", self._on_music_switch_toggled)
        self.track_dropdown.connect("notify::selected", self._on_track_selected)
        self.music_file_button.connect("clicked", self._on_choose_audio_file)
        self.music_play_button.connect("clicked", lambda *_: self.audio_service.toggle())
        self.volume_scale.connect("value-changed", self._on_volume_changed)

    def _setup_audio_tracks(self):
        tracks = self.audio_service.get_track_list()
        self.track_dropdown.set_model(Gtk.StringList.new(tracks))

    def _sync_view(self):
        self.timer_label.set_label(format_time(self.timer_service.seconds_left))
        self._update_status_label()
        self._update_stats_display()

    # Mode switching
    def _on_mode_button_toggled(self, button, mode):
        if button.get_active():
            self.timer_service.set_mode(mode)

    # Timer callbacks
    def _on_timer_tick(self, seconds_left, total_seconds, fraction):
        self.timer_label.set_label(format_time(seconds_left))
        self.progress_bar.set_fraction(fraction)
        if self.timer_service.mode == MODE_FOCUS:
            self._update_stats_display()

    def _on_timer_state_changed(self, mode, running, seconds_left, total_seconds, fraction):
        self.timer_label.set_label(format_time(seconds_left))
        self.progress_bar.set_fraction(fraction)
        self.start_button.set_label("Pause" if running else "Start")
        self._update_status_label()

    def _on_timer_complete(self, mode, sessions_completed):
        if self.settings_service.is_sound_enabled():
            display = Gdk.Display.get_default()
            if display:
                display.beep()

        mode_name = MODE_TITLES.get(mode, "Session")
        toast = Adw.Toast.new(f"{mode_name} complete!")
        toast.set_timeout(3)
        self.toast_overlay.add_toast(toast)
        self._update_stats_display()

    # Audio controls & file chooser 
    def _on_music_switch_toggled(self, switch, _pspec):
        active = switch.get_active()
        self.music_controls_box.set_sensitive(active)
        if not active:
            self.audio_service.stop()

    def _on_track_selected(self, dropdown, _pspec):
        idx = dropdown.get_selected()
        if idx < len(self.audio_service.preset_tracks):
            self.audio_service.select_preset_track(idx)

    def _on_choose_audio_file(self, button):
        # Open file dialog for local audio selection
        try:
            dialog = Gtk.FileDialog.new()
            dialog.set_title("Select Ambient Audio File")

            audio_filter = Gtk.FileFilter()
            audio_filter.set_name("Audio Files (*.mp3, *.ogg, *.flac, *.wav)")
            audio_filter.add_mime_type("audio/*")
            dialog.set_default_filter(audio_filter)

            window = self.get_root()
            dialog.open(window if isinstance(window, Gtk.Window) else None, None, self._on_file_dialog_finish)
        except Exception:
            pass

    def _on_file_dialog_finish(self, dialog, result):
        try:
            file = dialog.open_finish(result)
            if file:
                path = file.get_path()
                self.audio_service.set_custom_file(path)
                self._setup_audio_tracks()
                self.track_dropdown.set_selected(len(self.audio_service.preset_tracks))
        except Exception:
            pass

    def _on_volume_changed(self, scale):
        val = scale.get_value() / 100.0
        self.audio_service.set_volume(val)

    def _on_audio_state_changed(self, is_playing, current_track, volume):
        icon = "media-playback-pause-symbolic" if is_playing else "media-playback-start-symbolic"
        self.music_play_button.set_icon_name(icon)

    # Status and Stats display
    def _update_status_label(self):
        state = "In Progress" if self.timer_service.running else "Ready"
        mode_title = MODE_TITLES.get(self.timer_service.mode, "Focus")
        self.status_label.set_label(f"● {mode_title} · {state}")

    def _update_stats_display(self):
        self.sessions_today_value.set_label(format_sessions(self.timer_service.sessions_completed))
        self.focus_time_value.set_label(format_focus_time(self.timer_service.focus_seconds_total))
