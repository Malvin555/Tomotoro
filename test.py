import gi

gi.require_version("Gtk", "4.0")
gi.require_version("Gdk", "4.0")

from gi.repository import Gdk, Gtk

display = Gdk.Display.get_default()
theme = Gtk.IconTheme.get_for_display(display)

print("alarm-symbolic:", theme.has_icon("alarm-symbolic"))
print("chart-symbolic:", theme.has_icon("chart-symbolic"))
print("open-menu-symbolic:", theme.has_icon("open-menu-symbolic"))
