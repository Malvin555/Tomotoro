from gi.repository import GLib, Gtk


class MarqueeLabel:
    def __init__(
        self,
        scrolled_window: Gtk.ScrolledWindow,
        label: Gtk.Label,
        speed_px: int = 1,
        pause_ms: int = 1200,
        step_ms: int = 40,
    ):
        self.scrolled = scrolled_window
        self.label = label
        self.speed = speed_px
        self.pause_ms = pause_ms
        self.step_ms = step_ms
        self._scroll_source = None
        self._pause_source = None
        self._text = None

        self.scrolled.get_hadjustment().connect("changed", self._on_adjustment_changed)

    def set_text(self, text: str):
        if text == self._text:
            return
        self._text = text
        self.label.set_label(text)
        self.stop()

    def stop(self):
        if self._scroll_source is not None:
            GLib.source_remove(self._scroll_source)
            self._scroll_source = None
        if self._pause_source is not None:
            GLib.source_remove(self._pause_source)
            self._pause_source = None
        adjustment = self.scrolled.get_hadjustment()
        if adjustment is not None:
            adjustment.set_value(0)

    def _on_adjustment_changed(self, adjustment):
        if self._scroll_source or self._pause_source:
            return
        adjustment.set_value(0)
        overflow = adjustment.get_upper() - adjustment.get_page_size()
        if overflow > 2:
            self._pause_source = GLib.timeout_add(self.pause_ms, self._start_scroll)

    def _start_scroll(self):
        self._pause_source = None
        self._scroll_source = GLib.timeout_add(self.step_ms, self._tick)
        return False

    def _tick(self):
        adjustment = self.scrolled.get_hadjustment()
        max_value = adjustment.get_upper() - adjustment.get_page_size()
        if max_value <= 0:
            self._scroll_source = None
            return False

        new_value = adjustment.get_value() + self.speed
        if new_value >= max_value:
            adjustment.set_value(max_value)
            self._scroll_source = None
            self._pause_source = GLib.timeout_add(self.pause_ms, self._reset_and_loop)
            return False

        adjustment.set_value(new_value)
        return True

    def _reset_and_loop(self):
        self.scrolled.get_hadjustment().set_value(0)
        self._pause_source = GLib.timeout_add(self.pause_ms, self._start_scroll)
        return False
