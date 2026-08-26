from gi.repository import Adw, Gdk, Gio, Gtk

from ..constant import MODE_TITLES
from ..services.analytics import AnalyticsService
from ..services.audio import AudioService
from ..services.settings import SettingsService
from ..services.timer import (
    MODE_FOCUS,
    MODE_LONG,
    MODE_SHORT,
    TimerService,
)
from ..utils.formatters import format_focus_time, format_sessions, format_time
from ..utils.marquee import MarqueeLabel
from ..utils.stat_viz import LiveStatViz
from ..utils.track_dropdown import TrackDropDown


@Gtk.Template(resource_path="/org/maldoro/fyvin/pomodoro.ui")
class PomodoroView(Gtk.Box):
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
    title_scroll = Gtk.Template.Child()
    title_label = Gtk.Template.Child()
    track_picker_box = Gtk.Template.Child()
    music_file_button = Gtk.Template.Child()
    music_play_button = Gtk.Template.Child()
    volume_scale = Gtk.Template.Child()
    sessions_today_value = Gtk.Template.Child()
    focus_time_value = Gtk.Template.Child()
    sessions_viz_box = Gtk.Template.Child()
    focus_viz_box = Gtk.Template.Child()

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        self.timer_service = TimerService()
        self.audio_service = AudioService.get_default()
        self.analytics_service = AnalyticsService.get_default()
        self.timer_service.on_complete_callbacks.append(
            self.analytics_service.record_session
        )
        self.audio_service.on_state_change_callbacks.append(
            self.analytics_service.record_audio_state
        )
        self.settings_service = SettingsService.get_default()
        self.title_marquee = MarqueeLabel(self.title_scroll, self.title_label)
        self._was_running = False

        self.track_dropdown = TrackDropDown()
        self.track_picker_box.append(self.track_dropdown)

        self.sessions_viz = LiveStatViz(mode="sessions")
        self.focus_viz = LiveStatViz(mode="focus")
        self.sessions_viz_box.append(self.sessions_viz)
        self.focus_viz_box.append(self.focus_viz)

        self._setup_signals()
        self._setup_audio_tracks()
        self._sync_view()
        self.title_marquee.set_text(self.audio_service.current_track_name)
        self._update_music_gate()

    def _setup_signals(self):
        self.timer_service.on_tick_callbacks.append(self._on_timer_tick)
        self.timer_service.on_complete_callbacks.append(self._on_timer_complete)
        self.timer_service.on_state_change_callbacks.append(
            self._on_timer_state_changed
        )

        self.audio_service.on_state_change_callbacks.append(
            self._on_audio_state_changed
        )
        self.audio_service.on_tracks_change_callbacks.append(
            self._on_tracks_changed
        )

        self.mode_focus_toggle.connect(
            "toggled", self._on_mode_button_toggled, MODE_FOCUS
        )
        self.mode_short_toggle.connect(
            "toggled", self._on_mode_button_toggled, MODE_SHORT
        )
        self.mode_long_toggle.connect(
            "toggled", self._on_mode_button_toggled, MODE_LONG
        )

        self.start_button.connect("clicked", lambda *_: self.timer_service.toggle())
        self.reset_button.connect("clicked", lambda *_: self.timer_service.reset())
        self.skip_button.connect("clicked", lambda *_: self.timer_service.skip())

        self.music_switch.connect("notify::active", self._on_music_switch_toggled)
        self.track_dropdown.connect("track-selected", self._on_track_selected)
        self.music_file_button.connect("clicked", self._on_choose_audio_file)
        self.music_play_button.connect("clicked", self._on_music_play_clicked)
        self.volume_scale.connect("value-changed", self._on_volume_changed)

    def _setup_audio_tracks(self):
        tracks = self.audio_service.get_track_list()
        selected = min(self.audio_service.current_index, max(0, len(tracks) - 1))
        self.track_dropdown.set_tracks(tracks, selected)

    def _on_tracks_changed(self, _tracks):
        self._setup_audio_tracks()

    def _sync_view(self):
        self.timer_label.set_label(format_time(self.timer_service.seconds_left))
        self._update_status_label()
        self._update_stats_display()
        self._update_mode_lock()
        self._update_music_gate()

    def _on_mode_button_toggled(self, button, mode):
        if self.timer_service.running:
            # Revert UI to the active mode; changes are locked while running.
            self._sync_mode_toggles()
            return
        if button.get_active():
            self.timer_service.set_mode(mode)

    def _sync_mode_toggles(self):
        mode = self.timer_service.mode
        self.mode_focus_toggle.set_active(mode == MODE_FOCUS)
        self.mode_short_toggle.set_active(mode == MODE_SHORT)
        self.mode_long_toggle.set_active(mode == MODE_LONG)

    def _update_mode_lock(self):
        locked = self.timer_service.running
        for button in (
            self.mode_focus_toggle,
            self.mode_short_toggle,
            self.mode_long_toggle,
        ):
            button.set_sensitive(not locked)

    def _update_music_gate(self):
        """Music can only be used while a Pomodoro session is running."""
        running = self.timer_service.running
        self.music_controls_box.set_sensitive(running)
        self.music_switch.set_sensitive(running)
        if not running and self.audio_service.is_playing:
            self.audio_service.stop()
        playing = running and self.audio_service.is_playing
        self.title_marquee.set_active(playing)
        self.track_dropdown.set_marquee_active(playing)

    def _on_timer_tick(self, seconds_left, total_seconds, fraction):
        self.timer_label.set_label(format_time(seconds_left))
        self.progress_bar.set_fraction(fraction)
        if self.timer_service.mode == MODE_FOCUS:
            self._update_stats_display()

    def _on_timer_state_changed(
        self, mode, running, seconds_left, total_seconds, fraction
    ):
        self.timer_label.set_label(format_time(seconds_left))
        self.progress_bar.set_fraction(fraction)
        self.start_button.set_label("Pause" if running else "Start")
        self._update_status_label()
        self._update_stats_display()
        self._update_mode_lock()
        self._sync_music_with_timer(running)
        self._update_music_gate()

    def _sync_music_with_timer(self, running: bool):
        if running and not self._was_running:
            if self.settings_service.is_play_music_with_timer():
                if not self.music_switch.get_active():
                    self.music_switch.set_active(True)
                self.audio_service.play()
        elif not running and self._was_running:
            self.audio_service.stop()
            # Allow choosing music intent again only after stop/skip/complete.
            # Switch stays as-is but gated off until next start.
        self._was_running = running

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
        self.audio_service.stop()
        self._was_running = False
        self._update_mode_lock()
        self._update_music_gate()

    def _on_music_switch_toggled(self, switch, _pspec):
        if not self.timer_service.running:
            if switch.get_active():
                switch.set_active(False)
            self._update_music_gate()
            return

        if not switch.get_active():
            self.audio_service.stop()
        self._update_music_gate()

    def _on_music_play_clicked(self, _button):
        if not self.timer_service.running:
            toast = Adw.Toast.new("Start a Pomodoro session to play music")
            toast.set_timeout(2)
            self.toast_overlay.add_toast(toast)
            return
        if not self.music_switch.get_active():
            self.music_switch.set_active(True)
        self.audio_service.toggle()

    def _on_track_selected(self, _picker, index: int):
        self.audio_service.select_track(index)

    def _on_choose_audio_file(self, button):
        try:
            dialog = Gtk.FileDialog.new()
            dialog.set_title("Add Ambient Audio")

            audio_filter = Gtk.FileFilter()
            audio_filter.set_name("Audio Files (*.mp3, *.ogg, *.flac, *.wav)")
            audio_filter.add_mime_type("audio/*")
            for pattern in ("*.mp3", "*.ogg", "*.flac", "*.wav", "*.opus", "*.m4a"):
                audio_filter.add_pattern(pattern)
            dialog.set_default_filter(audio_filter)

            filters = Gio.ListStore.new(Gtk.FileFilter)
            filters.append(audio_filter)
            dialog.set_filters(filters)

            window = self.get_root()
            dialog.open(
                window if isinstance(window, Gtk.Window) else None,
                None,
                self._on_file_dialog_finish,
            )
        except Exception:
            pass

    def _on_file_dialog_finish(self, dialog, result):
        try:
            file = dialog.open_finish(result)
            if file:
                path = file.get_path()
                self.audio_service.set_custom_file(path)
                self._setup_audio_tracks()
                if (
                    self.timer_service.running
                    and self.music_switch.get_active()
                ):
                    self.audio_service.play()
        except Exception:
            pass

    def _on_volume_changed(self, scale):
        val = scale.get_value() / 100.0
        self.audio_service.set_volume(val)

    def _on_audio_state_changed(self, is_playing, current_track_name, volume):
        # Enforce: never keep audio playing if Pomodoro is not running.
        if is_playing and not self.timer_service.running:
            self.audio_service.stop()
            return

        icon = (
            "media-playback-pause-symbolic"
            if is_playing
            else "media-playback-start-symbolic"
        )
        self.music_play_button.set_icon_name(icon)
        self.title_marquee.set_text(current_track_name)
        self.track_dropdown.set_selected(self.audio_service.current_index)
        playing = self.timer_service.running and is_playing
        self.title_marquee.set_active(playing)
        self.track_dropdown.set_marquee_active(playing)

    def _update_status_label(self):
        state = "In Progress" if self.timer_service.running else "Ready"
        mode_title = MODE_TITLES.get(self.timer_service.mode, "Focus")
        self.status_label.set_label(f"● {mode_title} · {state}")

    def _update_stats_display(self):
        sessions = self.timer_service.sessions_completed
        focus_seconds = self.timer_service.focus_seconds_total
        running = self.timer_service.running

        self.sessions_today_value.set_label(format_sessions(sessions))
        self.focus_time_value.set_label(format_focus_time(focus_seconds))

        self.sessions_viz.set_value(sessions)
        self.sessions_viz.set_active(running)
        self.focus_viz.set_value(focus_seconds)
        self.focus_viz.set_active(running)
