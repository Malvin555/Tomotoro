from gi.repository import Adw, GObject, Gtk

from .analytics import AnalyticsView
from .pomodoro import PomodoroView


@Gtk.Template(resource_path="/org/maldoro/fyvin/window.ui")
class MaldoroWindow(Adw.ApplicationWindow):
    __gtype_name__ = "MaldoroWindow"

    stack = Gtk.Template.Child()
    view_switcher_title = Gtk.Template.Child()
    view_switcher_bar = Gtk.Template.Child()
    pomodoro_view = Gtk.Template.Child()
    analytics_view = Gtk.Template.Child()

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        self.view_switcher_title.bind_property(
            "title-visible",
            self.view_switcher_bar,
            "reveal",
            GObject.BindingFlags.SYNC_CREATE,
        )

        # display = self.get_display()
        # theme = Gtk.IconTheme.get_for_display(display)

        # print("alarm-symbolic:", theme.has_icon("alarm-symbolic"))
        # print("open-menu-symbolic:", theme.has_icon("open-menu-symbolic"))
