from gi.repository import Adw, Gtk

# Register template child types used by window.ui
from .analytics import AnalyticsView  # noqa: F401
from .pomodoro import PomodoroView  # noqa: F401


@Gtk.Template(resource_path="/org/maldoro/fyvin/window.ui")
class MaldoroWindow(Adw.ApplicationWindow):
    __gtype_name__ = "MaldoroWindow"

    header_bar = Gtk.Template.Child()
    stack = Gtk.Template.Child()
    view_switcher = Gtk.Template.Child()
    view_switcher_bar = Gtk.Template.Child()
    pomodoro_view = Gtk.Template.Child()
    analytics_view = Gtk.Template.Child()

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._window_title = Adw.WindowTitle(title="MalDoro")
        self._setup_adaptive_navigation()

    def _setup_adaptive_navigation(self):
        """Top tabs when wide; bottom bar when narrow (GNOME / libadwaita pattern)."""
        narrow = Adw.Breakpoint.new(Adw.BreakpointCondition.parse("max-width: 550sp"))
        narrow.add_setter(self.header_bar, "title-widget", self._window_title)
        narrow.add_setter(self.view_switcher_bar, "reveal", True)
        self.add_breakpoint(narrow)
