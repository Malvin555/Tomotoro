from gi.repository import Adw, Gdk, Gio, Gtk

from ..constant import MODE_FOCUS, MODE_TITLES
from ..services.analytics import AnalyticsService
from ..services.audio import AudioService
from ..services.settings import SettingsService
from ..services.timer import TimerService
from ..utils.formatters import format_focus_time, format_sessions, format_time
from ..utils.marquee import MarqueeLabel
from ..utils.stat_viz import LiveStatViz
from ..utils.track_dropdown import TrackDropDown
from .helpers import ModeSwitcher, MusicSessionGate


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

        self.timer = TimerService()
        self.audio = AudioService.get_default()
        self.analytics = AnalyticsService.get_default()
        self.settings = SettingsService.get_default()

        self.timer.on_complete_callbacks.append(self.analytics.record_session)
        self.audio.on_state_change_callbacks.append(self.analytics.record_audio_state)

        self.title_marquee = MarqueeLabel(self.title_scroll, self.title_label)
        self.track_dropdown = TrackDropDown()
        self.track_picker_box.append(self.track_dropdown)

        self.sessions_viz = LiveStatViz(mode="sessions")
        self.focus_viz = LiveStatViz(mode="focus")
        self.sessions_viz_box.append(self.sessions_viz)
        self.focus_viz_box.append(self.focus_viz)

        self.mode_switcher = ModeSwitcher(
            self.mode_focus_toggle,
            self.mode_short_toggle,
            self.mode_long_toggle,
            on_mode_chosen=self.timer.set_mode,
        )
        self.music_gate = MusicSessionGate(
            self.music_switch,
            self.music_controls_box,
            self.title_marquee,
            self.track_dropdown,
            self.audio,
        )

        self._was_running = False
        self._connect_signals()
        self._reload_tracks()
        self._sync_view()
        self.title_marquee.set_text(self.audio.current_track_name)

    def _connect_signals(self):
        self.timer.on_tick_callbacks.append(self._on_timer_tick)
        self.timer.on_complete_callbacks.append(self._on_timer_finished)
        self.timer.on_skip_callbacks.append(self._on_timer_skipped)
        self.timer.on_state_change_callbacks.append(self._on_timer_state_changed)

        self.audio.on_state_change_callbacks.append(self._on_audio_state_changed)
        self.audio.on_tracks_change_callbacks.append(lambda _t: self._reload_tracks())

        self.start_button.connect("clicked", lambda *_: self.timer.toggle())
        self.reset_button.connect("clicked", lambda *_: self.timer.reset())
        self.skip_button.connect("clicked", lambda *_: self.timer.skip())

        self.music_switch.connect("notify::active", self._on_music_switch_toggled)
        self.track_dropdown.connect("track-selected", self._on_track_selected)
        self.music_file_button.connect("clicked", self._on_choose_audio_file)
        self.music_play_button.connect("clicked", self._on_music_play_clicked)
        self.volume_scale.connect("value-changed", self._on_volume_changed)

    def _reload_tracks(self):
        tracks = self.audio.get_track_list()
        selected = min(self.audio.current_index, max(0, len(tracks) - 1))
        self.track_dropdown.set_tracks(tracks, selected)

    def _sync_view(self):
        self.timer_label.set_label(format_time(self.timer.seconds_left))
        self.mode_switcher.sync(self.timer.mode)
        self._update_status_label()
        self._update_stats()
        self.mode_switcher.set_locked(self.timer.running)
        self.music_gate.refresh(self.timer.running, self.audio.is_playing)

    def _on_timer_tick(self, seconds_left, total_seconds, fraction):
        self.timer_label.set_label(format_time(seconds_left))
        self.progress_bar.set_fraction(fraction)
        if self.timer.mode == MODE_FOCUS:
            self._update_stats()

    def _on_timer_state_changed(
        self, mode, running, seconds_left, total_seconds, fraction
    ):
        self.timer_label.set_label(format_time(seconds_left))
        self.progress_bar.set_fraction(fraction)
        self.start_button.set_label("Pause" if running else "Start")
        self.mode_switcher.sync(mode)
        self._update_status_label()
        self._update_stats()
        self.mode_switcher.set_locked(running)
        self._sync_music_with_timer(running)
        self.music_gate.refresh(running, self.audio.is_playing)

    def _on_timer_finished(self, mode, sessions_completed):
        if self.settings.is_sound_enabled():
            display = Gdk.Display.get_default()
            if display:
                display.beep()

        toast = Adw.Toast.new(f"{MODE_TITLES.get(mode, 'Session')} complete!")
        toast.set_timeout(3)
        self.toast_overlay.add_toast(toast)

        self.audio.stop()
        self._was_running = False
        self._update_stats()
        self.mode_switcher.set_locked(False)
        self.music_gate.refresh(False, False)

    def _on_timer_skipped(self, mode):
        toast = Adw.Toast.new(f"{MODE_TITLES.get(mode, 'Session')} skipped")
        toast.set_timeout(2)
        self.toast_overlay.add_toast(toast)

        self.audio.stop()
        self._was_running = False
        self._update_stats()
        self.mode_switcher.set_locked(False)
        self.music_gate.refresh(False, False)

    def _sync_music_with_timer(self, running: bool):
        if running and not self._was_running:
            if self.settings.is_play_music_with_timer():
                if not self.music_switch.get_active():
                    self.music_switch.set_active(True)
                self.audio.play()
        elif not running and self._was_running:
            self.audio.stop()
        self._was_running = running

    def _on_music_switch_toggled(self, switch, _pspec):
        if not self.timer.running:
            if switch.get_active():
                switch.set_active(False)
            self.music_gate.refresh(False, False)
            return
        if not switch.get_active():
            self.audio.stop()
        self.music_gate.refresh(True, self.audio.is_playing)

    def _on_music_play_clicked(self, _button):
        if not self.timer.running:
            toast = Adw.Toast.new("Start a Pomodoro session to play music")
            toast.set_timeout(2)
            self.toast_overlay.add_toast(toast)
            return
        if not self.music_switch.get_active():
            self.music_switch.set_active(True)
        self.audio.toggle()

    def _on_track_selected(self, _picker, index: int):
        self.audio.select_track(index)

    def _on_choose_audio_file(self, _button):
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
            if not file:
                return
            self.audio.set_custom_file(file.get_path())
            self._reload_tracks()
            if self.timer.running and self.music_switch.get_active():
                self.audio.play()
        except Exception:
            pass

    def _on_volume_changed(self, scale):
        self.audio.set_volume(scale.get_value() / 100.0)

    def _on_audio_state_changed(self, is_playing, current_track_name, volume):
        if is_playing and not self.timer.running:
            self.audio.stop()
            return

        self.music_play_button.set_icon_name(
            "media-playback-pause-symbolic"
            if is_playing
            else "media-playback-start-symbolic"
        )
        self.title_marquee.set_text(current_track_name)
        self.track_dropdown.set_selected(self.audio.current_index)
        self.music_gate.refresh(self.timer.running, is_playing)

    def _update_status_label(self):
        state = "In Progress" if self.timer.running else "Ready"
        mode_title = MODE_TITLES.get(self.timer.mode, "Focus")
        self.status_label.set_label(f"● {mode_title} · {state}")

    def _update_stats(self):
        sessions = self.timer.sessions_completed
        focus_seconds = self.timer.focus_seconds_total
        running = self.timer.running

        self.sessions_today_value.set_label(format_sessions(sessions))
        self.focus_time_value.set_label(format_focus_time(focus_seconds))
        self.sessions_viz.set_value(sessions)
        self.sessions_viz.set_active(running)
        self.focus_viz.set_value(focus_seconds)
        self.focus_viz.set_active(running)
