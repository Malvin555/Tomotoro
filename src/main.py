# main.py
#
# Copyright 2026 Malvin
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License along
# with this program; if not, write to the Free Software Foundation, Inc.,
# 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301 USA.
#
# SPDX-License-Identifier: GPL-2.0-or-later

import sys
from gettext import gettext as _

import gi

gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")

from gi.repository import Adw, Gio, Gtk, Gdk

from .view.preferences import MaldoroPreferences
from .view.window import MaldoroWindow


class MaldoroApplication(Adw.Application):
    """The main application singleton class."""

    def __init__(self, version=None):
        super().__init__(
            application_id="org.maldoro.fyvin",
            flags=Gio.ApplicationFlags.DEFAULT_FLAGS,
            resource_base_path="/org/maldoro/fyvin",
        )
        self._version = version

        self.create_action("quit", lambda *_: self.quit(), ["<control>q"])
        self.create_action("about", self.on_about_action)
        self.create_action("preferences", self.on_preferences_action)
        self.create_action("pomodoro", self.on_pomodoro_action)

    def do_startup(self):
        Gtk.Application.do_startup(self)
        self._setup_css()

    def _setup_css(self):
        provider = Gtk.CssProvider()
        try:
            provider.load_from_resource("/org/maldoro/fyvin/style.css")
            display = Gdk.Display.get_default()
            if display:
                Gtk.StyleContext.add_provider_for_display(
                    display, provider, Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION
                )
        except Exception as e:
            print(f"Could not load custom CSS: {e}")

    def do_activate(self):
        """Called when the application is activated.

        We raise the application's main window, creating it if
        necessary.
        """
        win = self.props.active_window
        if not win:
            win = MaldoroWindow(application=self)
        win.present()

    def on_about_action(self, *args):
        """Callback for the app.about action."""
        about = Adw.AboutDialog(
            application_name="MalDoro",
            application_icon="org.maldoro.fyvin",
            developer_name="Malvin",
            version=self._version,
            translator_credits=_("translator-credits"),
            developers=["Malvin"],
            copyright="© 2026 Malvin",
        )
        about.present(self.props.active_window)

    def on_preferences_action(self, widget, _):
        """Callback for the app.preferences action."""
        win = self.props.active_window
        prefs = MaldoroPreferences()
        prefs.present(win)

    def on_pomodoro_action(self, *args):
        """Open the Pomodoro UI (UI-only)."""
        win = self.props.active_window
        if win and hasattr(win, "show_pomodoro"):
            try:
                win.show_pomodoro()
            except Exception:
                print("Failed to show Pomodoro view")

    def create_action(self, name, callback, shortcuts=None):
        """Add an application action.

        Args:
            name: the name of the action
            callback: the function to be called when the action is
              activated
            shortcuts: an optional list of accelerators
        """
        action = Gio.SimpleAction.new(name, None)
        action.connect("activate", callback)
        self.add_action(action)
        if shortcuts:
            self.set_accels_for_action(f"app.{name}", shortcuts)


def main(version):
    """The application's entry point."""
    Adw.init()
    app = MaldoroApplication(version=version)
    return app.run(sys.argv)
