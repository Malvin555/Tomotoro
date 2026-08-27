from gi.repository import Adw, Gio, Gtk

from ..services.audio import AudioService
from ..services.settings import SettingsService
from ..utils.formatters import track_display_name


@Gtk.Template(resource_path="/org/tomotoro/fyvin/preferences.ui")
class TomotoroPreferences(Adw.PreferencesDialog):
    __gtype_name__ = "TomotoroPreferences"

    focus_length_row = Gtk.Template.Child()
    short_break_row = Gtk.Template.Child()
    long_break_row = Gtk.Template.Child()
    sessions_row = Gtk.Template.Child()
    auto_start_breaks_row = Gtk.Template.Child()
    auto_start_focus_row = Gtk.Template.Child()
    sound_row = Gtk.Template.Child()
    play_with_timer_row = Gtk.Template.Child()
    add_files_button = Gtk.Template.Child()
    add_folder_button = Gtk.Template.Child()
    custom_tracks_group = Gtk.Template.Child()

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.settings_service = SettingsService.get_default()
        self.audio_service = AudioService.get_default()
        self._track_rows = []
        self._empty_row = None

        self._bind_settings()
        self._setup_music_page()
        self._rebuild_track_list()

    def _bind_settings(self):
        self.settings_service.bind("focus-length", self.focus_length_row, "value")
        self.settings_service.bind("short-break-length", self.short_break_row, "value")
        self.settings_service.bind("long-break-length", self.long_break_row, "value")
        self.settings_service.bind(
            "sessions-until-long-break", self.sessions_row, "value"
        )
        self.settings_service.bind(
            "auto-start-breaks", self.auto_start_breaks_row, "active"
        )
        self.settings_service.bind(
            "auto-start-focus", self.auto_start_focus_row, "active"
        )
        self.settings_service.bind("sound-enabled", self.sound_row, "active")
        self.settings_service.bind(
            "play-music-with-timer", self.play_with_timer_row, "active"
        )

    def _setup_music_page(self):
        self.add_files_button.connect("clicked", self._on_add_files)
        self.add_folder_button.connect("clicked", self._on_add_folder)
        self.audio_service.on_tracks_change_callbacks.append(self._on_tracks_changed)

        self.connect("destroy", self._on_destroy)

    def _on_destroy(self, *_args):
        callbacks = self.audio_service.on_tracks_change_callbacks
        if self._on_tracks_changed in callbacks:
            callbacks.remove(self._on_tracks_changed)

    def _on_tracks_changed(self, _tracks):
        self._rebuild_track_list()

    def _audio_filter(self) -> Gtk.FileFilter:
        audio_filter = Gtk.FileFilter()
        audio_filter.set_name("Audio Files")
        for pattern in (
            "*.mp3",
            "*.ogg",
            "*.oga",
            "*.opus",
            "*.flac",
            "*.wav",
            "*.m4a",
            "*.aac",
        ):
            audio_filter.add_pattern(pattern)
        audio_filter.add_mime_type("audio/*")
        return audio_filter

    def _on_add_files(self, _button):
        dialog = Gtk.FileDialog.new()
        dialog.set_title("Select Music Files")
        dialog.set_default_filter(self._audio_filter())

        filters = Gio.ListStore.new(Gtk.FileFilter)
        filters.append(self._audio_filter())
        dialog.set_filters(filters)

        dialog.open_multiple(self.get_root(), None, self._on_add_files_finish)

    def _on_add_files_finish(self, dialog, result):
        try:
            files = dialog.open_multiple_finish(result)
        except Exception:
            return
        if not files:
            return

        paths = []
        for i in range(files.get_n_items()):
            file = files.get_item(i)
            path = file.get_path() if file else None
            if path:
                paths.append(path)

        added = self.audio_service.add_paths(paths)
        self._show_add_toast(added)

    def _on_add_folder(self, _button):
        dialog = Gtk.FileDialog.new()
        dialog.set_title("Select Music Folder")
        dialog.select_folder(self.get_root(), None, self._on_add_folder_finish)

    def _on_add_folder_finish(self, dialog, result):
        try:
            folder = dialog.select_folder_finish(result)
        except Exception:
            return
        if not folder:
            return
        path = folder.get_path()
        if not path:
            return
        added = self.audio_service.add_paths([path])
        self._show_add_toast(added)

    def _show_add_toast(self, added: int):
        if added <= 0:
            message = "No supported audio files found"
        elif added == 1:
            message = "Added 1 track"
        else:
            message = f"Added {added} tracks"
        toast = Adw.Toast.new(message)
        toast.set_timeout(2)
        self.add_toast(toast)

    def _clear_track_rows(self):
        for row in self._track_rows:
            self.custom_tracks_group.remove(row)
        self._track_rows.clear()
        if self._empty_row is not None:
            self.custom_tracks_group.remove(self._empty_row)
            self._empty_row = None

    def _rebuild_track_list(self):
        self._clear_track_rows()
        tracks = self.audio_service.get_custom_tracks()

        if not tracks:
            row = Adw.ActionRow()
            row.set_title("No custom tracks yet")
            row.set_subtitle("Add files or a folder to use your own focus music")
            row.set_sensitive(False)
            self.custom_tracks_group.add(row)
            self._empty_row = row
            return

        for path in tracks:
            row = Adw.ActionRow()
            row.set_title(track_display_name(path))
            row.set_subtitle(path)
            row.set_tooltip_text(path)
            row.set_activatable(False)

            remove_button = Gtk.Button(
                icon_name="user-trash-symbolic",
                valign=Gtk.Align.CENTER,
                tooltip_text="Remove track",
            )
            remove_button.add_css_class("flat")
            remove_button.add_css_class("circular")
            remove_button.connect("clicked", self._on_remove_track, path)
            row.add_suffix(remove_button)
            self.custom_tracks_group.add(row)
            self._track_rows.append(row)

    def _on_remove_track(self, _button, path: str):
        self.audio_service.remove_custom_track(path)
        toast = Adw.Toast.new("Track removed")
        toast.set_timeout(2)
        self.add_toast(toast)
