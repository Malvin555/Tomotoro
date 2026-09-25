from gi.repository import Adw, Gtk

from .analytics import AnalyticsView  # noqa: F401
from .pomodoro import PomodoroView  # noqa: F401


@Gtk.Template(resource_path="/org/tomotoro/fyvin/window.ui")
class TomotoroWindow(Adw.ApplicationWindow):
    __gtype_name__ = "TomotoroWindow"

    header_bar = Gtk.Template.Child()
    stack = Gtk.Template.Child()
    view_switcher = Gtk.Template.Child()
    view_switcher_bar = Gtk.Template.Child()
    pomodoro_view = Gtk.Template.Child()
    analytics_view = Gtk.Template.Child()

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._window_title = Adw.WindowTitle(title="Tomotoro")
        self._setup_adaptive_navigation()
        self._setup_keyboard_shortcuts()

    def _setup_adaptive_navigation(self):
        narrow = Adw.Breakpoint.new(Adw.BreakpointCondition.parse("max-width: 550sp"))
        narrow.add_setter(self.header_bar, "title-widget", self._window_title)
        narrow.add_setter(self.view_switcher_bar, "reveal", True)
        self.add_breakpoint(narrow)

    def _setup_keyboard_shortcuts(self):
        """Setup Alt+1, Alt+2 keyboard shortcuts to switch tabs."""

        controller = Gtk.ShortcutController.new()
        controller.set_scope(Gtk.ShortcutScope.MANAGED)

        shortcut1 = Gtk.Shortcut.new(
            Gtk.ShortcutTrigger.parse_string("<Alt>1"),
            Gtk.CallbackAction.new(self._on_switch_to_pomodoro),
        )
        controller.add_shortcut(shortcut1)

        shortcut2 = Gtk.Shortcut.new(
            Gtk.ShortcutTrigger.parse_string("<Alt>2"),
            Gtk.CallbackAction.new(self._on_switch_to_analytics),
        )
        controller.add_shortcut(shortcut2)

        self.add_controller(controller)

    def _on_switch_to_pomodoro(self, *args):
        """Switch to the Pomodoro tab."""
        self.stack.set_visible_child_name("pomodoro")
        return True

    def _on_switch_to_analytics(self, *args):
        """Switch to the Analytics tab."""
        self.stack.set_visible_child_name("analytics")
        return True
