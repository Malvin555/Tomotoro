from gi.repository import GObject, Gtk, Pango

from .marquee import MarqueeDrawingArea


class TrackDropDown(Gtk.Box):
    """An adaptive, GNOME HIG compliant track dropdown selector.

    Matches width (w) precisely with the source select button, uses compact menu styling,
    prevents background scrolling on click/open, and provides comfortable in-place scrolling.
    """

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
        self._button.set_size_request(1, 34)
        self._button.set_focus_on_click(False)
        self._button.set_can_focus(False)
        self._button.add_css_class("track-dropdown-button")

        btn_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        btn_box.set_hexpand(True)
        btn_box.set_halign(Gtk.Align.FILL)
        btn_box.set_valign(Gtk.Align.CENTER)
        btn_box.set_size_request(1, -1)

        self._icon = Gtk.Image.new_from_icon_name("tomotoro-track-symbolic")
        self._icon.set_pixel_size(14)
        self._icon.add_css_class("dim-label")
        btn_box.append(self._icon)

        self._title = MarqueeDrawingArea(
            speed_px_per_sec=28.0, gap_px=36, font_desc="Sans 11"
        )
        self._title.set_hexpand(True)
        self._title.set_halign(Gtk.Align.FILL)
        self._title.set_valign(Gtk.Align.CENTER)
        self._title.set_content_height(16)
        self._title.set_size_request(1, -1)
        btn_box.append(self._title)

        self._button.set_child(btn_box)
        self.append(self._button)

        self._list = Gtk.ListBox()
        self._list.set_selection_mode(Gtk.SelectionMode.SINGLE)
        self._list.set_activate_on_single_click(True)
        self._list.set_can_focus(False)
        self._list.set_focus_on_click(False)
        self._list.set_hexpand(True)
        self._list.add_css_class("track-dropdown-list")
        self._list.connect("row-activated", self._on_row_activated)

        popover = Gtk.Popover()
        popover.set_position(Gtk.PositionType.BOTTOM)
        popover.set_autohide(True)
        popover.set_has_arrow(True)
        popover.set_can_focus(False)
        popover.add_css_class("track-dropdown-popover")
        popover.add_css_class("menu")

        scroller = Gtk.ScrolledWindow()
        scroller.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        scroller.set_max_content_height(170)
        scroller.set_propagate_natural_height(True)
        scroller.set_propagate_natural_width(False)
        scroller.set_hexpand(True)
        scroller.set_halign(Gtk.Align.FILL)
        scroller.set_can_focus(False)
        scroller.set_child(self._list)
        popover.set_child(scroller)

        self._scroller = scroller
        self._popover = popover
        self._button.set_popover(popover)

        self._button.connect("notify::active", self._sync_popover_width)
        popover.connect("map", self._sync_popover_width)
        popover.connect("notify::visible", self._sync_popover_width)

    def _sync_popover_width(self, *_args):
        """Ensures the popover width always matches the select button width (w)."""
        btn_width = self._button.get_width()
        if btn_width > 20:
            self._scroller.set_size_request(btn_width, -1)
            self._scroller.set_min_content_width(btn_width)
            self._scroller.set_max_content_width(btn_width)
            self._list.set_size_request(btn_width, -1)
            self._popover.set_size_request(btn_width, -1)

    def set_tracks(self, tracks: list, selected: int = 0):
        self._updating = True
        self._tracks = list(tracks)
        if self._tracks:
            selected = max(0, min(selected, len(self._tracks) - 1))
        else:
            selected = 0
        self._selected = selected
        self._rebuild_list()
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
        self._update_selection_checkmarks()

    def set_marquee_active(self, active: bool):
        self._title.set_active(active)

    def _update_title(self):
        if not self._tracks:
            self._title.set_text("No tracks")
            self._button.set_tooltip_text(None)
            return
        name = self._tracks[self._selected]
        self._title.set_text(name)
        self._button.set_tooltip_text(name)

    def _update_selection_checkmarks(self):
        index = 0
        while True:
            row = self._list.get_row_at_index(index)
            if row is None:
                break
            check = getattr(row, "_check_icon", None)
            if check is not None:
                check.set_visible(index == self._selected)
            index += 1

    def _rebuild_list(self):
        while True:
            row = self._list.get_row_at_index(0)
            if row is None:
                break
            self._list.remove(row)

        for index, name in enumerate(self._tracks):
            row_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
            row_box.set_margin_start(10)
            row_box.set_margin_end(10)
            row_box.set_margin_top(6)
            row_box.set_margin_bottom(6)
            row_box.set_hexpand(True)
            row_box.set_size_request(1, -1)

            label = Gtk.Label(label=name, xalign=0)
            label.set_ellipsize(Pango.EllipsizeMode.END)
            label.set_hexpand(True)
            label.set_size_request(1, -1)
            row_box.append(label)

            check = Gtk.Image.new_from_icon_name("object-select-symbolic")
            check.set_pixel_size(14)
            check.add_css_class("accent")
            check.set_visible(index == self._selected)
            row_box.append(check)

            row = Gtk.ListBoxRow()
            row.set_child(row_box)
            row.set_tooltip_text(name)
            row.set_can_focus(False)
            row.set_focus_on_click(False)
            row._track_index = index
            row._check_icon = check
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
        self._update_selection_checkmarks()
        self._popover.popdown()
        self.emit("track-selected", index)
