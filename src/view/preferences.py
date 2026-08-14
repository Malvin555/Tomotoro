# Preferences view controller
from gi.repository import Gtk, Adw
from ..services.settings import SettingsService


@Gtk.Template(resource_path="/org/maldoro/fyvin/preferences.ui")
class MaldoroPreferences(Adw.PreferencesDialog):
    """Preferences modal dialog controller."""

    __gtype_name__ = "MaldoroPreferences"

    focus_length_row = Gtk.Template.Child()
    short_break_row = Gtk.Template.Child()
    long_break_row = Gtk.Template.Child()
    sessions_row = Gtk.Template.Child()
    auto_start_breaks_row = Gtk.Template.Child()
    auto_start_focus_row = Gtk.Template.Child()
    sound_row = Gtk.Template.Child()

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.settings_service = SettingsService.get_default()
        self._bind_settings()

    def _bind_settings(self):
        self.settings_service.bind("focus-length", self.focus_length_row, "value")
        self.settings_service.bind("short-break-length", self.short_break_row, "value")
        self.settings_service.bind("long-break-length", self.long_break_row, "value")
        self.settings_service.bind("sessions-until-long-break", self.sessions_row, "value")
        self.settings_service.bind("auto-start-breaks", self.auto_start_breaks_row, "active")
        self.settings_service.bind("auto-start-focus", self.auto_start_focus_row, "active")
        self.settings_service.bind("sound-enabled", self.sound_row, "active")
