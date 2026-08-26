from gi.repository import GObject, Gtk, Pango

from .marquee import MarqueeDrawingArea


class TrackDropDown(Gtk.Box):
    __gsignals__ = {
        "track-selected": (GObject.SignalFlags.RUN_FIRST, None, (int,)),
    }

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.set_orientation(Gtk.Orientation.HORIZONTAL)
        self.set_hexpand(True)
        self.set_halign(Gtk.Align.FILL)
        self.set_size_request(1, -1)
        self.add_css_class("track-dropdown")

        self._tracks = []
        self._selected = 0
        self._updating = False

        self._button = Gtk.MenuButton()
        self._button.set_hexpand(True)
        self._button.set_halign(Gtk.Align.FILL)
        self._button.set_always_show_arrow(True)
        self._button.add_css_class("track-dropdown-button")

        self._title = MarqueeDrawingArea(speed_px=1.0, gap_px=40, step_ms=30)
        self._title.set_font_desc("Sans 12")
        self._title.set_hexpand(True)
        self._title.set_valign(Gtk.Align.CENTER)
        self._title.set_content_height(18)

        self._button.set_child(self._title)
        self.append(self._button)

        self._list = Gtk.ListBox()
        self._list.set_selection_mode(Gtk.SelectionMode.SINGLE)
        self._list.set_activate_on_single_click(True)
        self._list.connect("row-activated", self._on_row_activated)

        popover = Gtk.Popover()
        popover.set_position(Gtk.PositionType.BOTTOM)
        popover.set_autohide(True)
        popover.set_has_arrow(True)

        scroller = Gtk.ScrolledWindow()
        scroller.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        scroller.set_max_content_height(260)
        scroller.set_max_content_width(280)
        scroller.set_propagate_natural_height(True)
        scroller.set_propagate_natural_width(True)
        scroller.set_size_request(200, -1)
        scroller.set_child(self._list)
        popover.set_child(scroller)

        self._button.set_popover(popover)
        self._popover = popover

    def set_tracks(self, tracks: list, selected: int = 0):
        self._updating = True
        self._tracks = list(tracks)
        self._rebuild_list()
        if self._tracks:
            selected = max(0, min(selected, len(self._tracks) - 1))
        else:
            selected = 0
        self._selected = selected
        self._update_title()
        self._updating = False

    def get_selected(self) -> int:
        return self._selected

    def set_selected(self, index: int):
        if not self._tracks:
            return
        index = max(0, min(index, len(self._tracks) - 1))
        self._selected = index
        self._update_title()
        row = self._list.get_row_at_index(index)
        if row is not None:
            self._list.select_row(row)

    def set_marquee_active(self, active: bool):
        self._title.set_active(active)

    def _update_title(self):
        if not self._tracks:
            self._title.set_text("No tracks")
            return
        name = self._tracks[self._selected]
        self._title.set_text(name)
        self._button.set_tooltip_text(name)

    def _rebuild_list(self):
        while True:
            row = self._list.get_row_at_index(0)
            if row is None:
                break
            self._list.remove(row)

        for index, name in enumerate(self._tracks):
            label = Gtk.Label(label=name, xalign=0)
            label.set_ellipsize(Pango.EllipsizeMode.END)
            label.set_max_width_chars(28)
            label.set_width_chars(28)
            label.set_hexpand(True)
            label.set_tooltip_text(name)

            row = Gtk.ListBoxRow()
            row.set_child(label)
            row._track_index = index
            self._list.append(row)

        if self._tracks:
            row = self._list.get_row_at_index(self._selected)
            if row is not None:
                self._list.select_row(row)

    def _on_row_activated(self, _list, row):
        if self._updating:
            return
        index = getattr(row, "_track_index", -1)
        if index < 0:
            return
        self._selected = index
        self._update_title()
        self._popover.popdown()
        self.emit("track-selected", index)
