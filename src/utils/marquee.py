from gi.repository import GLib, Gtk, Pango, PangoCairo


class MarqueeDrawingArea(Gtk.DrawingArea):
    """Fixed-width endless marquee. Never expands the parent for long text.

    Scrolls only while active (e.g. music playing). When inactive, text is
    clipped/static at the start. Loops seamlessly with no end pause.
    """

    def __init__(self, speed_px: float = 1.0, gap_px: int = 48, step_ms: int = 30, **kwargs):
        super().__init__(**kwargs)
        self.speed = speed_px
        self.gap = gap_px
        self.step_ms = step_ms
        self._text = ""
        self._active = False
        self._offset = 0.0
        self._tick_id = None
        self._text_width = 0
        self._text_height = 16
        self._font = Pango.FontDescription.from_string("Sans Bold 14")

        self.set_hexpand(True)
        self.set_halign(Gtk.Align.FILL)
        # Tiny natural width so long titles cannot grow the window.
        self.set_content_width(1)
        self.set_content_height(20)
        self.set_draw_func(self._draw)
        self.add_css_class("title-marquee")
        self.connect("map", lambda *_: self._sync_tick())
        self.connect("unmap", lambda *_: self._stop_tick())

    def set_font_desc(self, desc: str):
        self._font = Pango.FontDescription.from_string(desc)
        self._measure_text()
        self.queue_draw()

    def set_text(self, text: str):
        text = text or ""
        if text == self._text:
            return
        self._text = text
        self.set_tooltip_text(text)
        self._offset = 0.0
        self._measure_text()
        self._sync_tick()
        self.queue_draw()

    def set_active(self, active: bool):
        active = bool(active)
        if active == self._active:
            return
        self._active = active
        if not active:
            self._offset = 0.0
        self._sync_tick()
        self.queue_draw()

    def stop(self):
        self.set_active(False)

    def _measure_text(self):
        layout = self.create_pango_layout(self._text or " ")
        layout.set_font_description(self._font)
        layout.set_single_paragraph_mode(True)
        self._text_width, self._text_height = layout.get_pixel_size()
        self.set_content_height(max(18, self._text_height + 2))

    def _needs_scroll(self) -> bool:
        width = self.get_width()
        return bool(self._text) and width > 1 and self._text_width > width + 2

    def _sync_tick(self):
        should_run = (
            self._active and self._needs_scroll() and self.get_mapped()
        )
        if should_run:
            self._ensure_tick()
        else:
            self._stop_tick()

    def _ensure_tick(self):
        if self._tick_id is None:
            self._tick_id = GLib.timeout_add(self.step_ms, self._on_tick)

    def _stop_tick(self):
        if self._tick_id is not None:
            GLib.source_remove(self._tick_id)
            self._tick_id = None

    def _on_tick(self):
        if not (self._active and self._needs_scroll()):
            self._tick_id = None
            return False
        cycle = self._text_width + self.gap
        if cycle <= 0:
            return True
        self._offset = (self._offset + self.speed) % cycle
        self.queue_draw()
        return True

    def _draw(self, _area, cr, width, height):
        if not self._text or width <= 1:
            return

        # Re-check scroll need after allocation changes.
        if self._active and self._needs_scroll() and self._tick_id is None:
            self._ensure_tick()

        layout = self.create_pango_layout(self._text)
        layout.set_font_description(self._font)
        layout.set_single_paragraph_mode(True)

        style = self.get_style_context()
        color = style.get_color()
        cr.set_source_rgba(color.red, color.green, color.blue, color.alpha)

        y = max(0, (height - self._text_height) / 2)
        cr.rectangle(0, 0, width, height)
        cr.clip()

        if not self._needs_scroll() or not self._active:
            cr.move_to(0, y)
            PangoCairo.show_layout(cr, layout)
            return

        cycle = self._text_width + self.gap
        x = -self._offset
        while x < width:
            cr.move_to(x, y)
            PangoCairo.show_layout(cr, layout)
            x += cycle


class MarqueeLabel:
    """Adapter kept for existing call sites: hosts MarqueeDrawingArea in a scroll slot."""

    def __init__(self, scrolled_window: Gtk.ScrolledWindow, label: Gtk.Label, **kwargs):
        self.scrolled = scrolled_window
        self.label = label
        self.canvas = MarqueeDrawingArea(**kwargs)

        self.scrolled.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.NEVER)
        self.scrolled.set_propagate_natural_width(False)
        self.scrolled.set_propagate_natural_height(True)
        self.scrolled.set_hexpand(True)
        self.scrolled.set_halign(Gtk.Align.FILL)
        self.scrolled.add_css_class("title-scroll")
        self.scrolled.set_child(self.canvas)

        self.label.set_hexpand(False)

    def set_text(self, text: str):
        text = text or ""
        self.label.set_label(text)
        self.label.set_tooltip_text(text)
        self.canvas.set_text(text)

    def set_active(self, active: bool):
        self.canvas.set_active(active)

    def stop(self):
        self.canvas.stop()
