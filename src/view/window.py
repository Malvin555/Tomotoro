from gi.repository import Gtk, Adw

from .pomodoro import PomodoroView  


@Gtk.Template(resource_path="/org/maldoro/fyvin/window.ui")
class MaldoroWindow(Adw.ApplicationWindow):
    __gtype_name__ = "MaldoroWindow"

    pomodoro_view = Gtk.Template.Child()

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
