import cairo
from gi.repository import GLib, Gtk, Pango, PangoCairo


class MarqueeDrawingArea(Gtk.DrawingArea):
    """A high-performance, layout-safe scrolling marquee label for GTK4.

    Guarantees zero horizontal window expansion (min width = 1px) and uses
    GTK4 frame clock callbacks for smooth 60fps+ rendering with soft edge fades.
    """

    def __init__(
        self,
        speed_px_per_sec: float = 32.0,
        gap_px: int = 44,
        font_desc: str = "Sans Bold 13",
        **kwargs,
    ):
        super().__init__(**kwargs)
        self.speed = speed_px_per_sec
        self.gap = gap_px
        self._text = ""
        self._active = False
        self._offset = 0.0
        self._tick_id = None
        self._last_frame_time = 0
        self._text_width = 0
        self._text_height = 18
        self._font = Pango.FontDescription.from_string(font_desc)

        self.set_hexpand(True)
        self.set_halign(Gtk.Align.FILL)
        self.set_valign(Gtk.Align.CENTER)
        self.set_content_width(1)
        self.set_content_height(20)
        self.set_size_request(1, -1)

        self.set_draw_func(self._draw)
        self.add_css_class("title-marquee")

        self.connect("map", self._on_map)
        self.connect("unmap", self._on_unmap)

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
        self._last_frame_time = 0
        self._measure_text()
        self._sync_animation()
        self.queue_draw()

    def set_active(self, active: bool):
        active = bool(active)
        if active == self._active:
            return
        self._active = active
        if not active:
            self._offset = 0.0
            self._last_frame_time = 0
        self._sync_animation()
        self.queue_draw()

    def stop(self):
        self.set_active(False)

    def _measure_text(self):
        if not self._text:
            self._text_width = 0
            self._text_height = 16
            return
        layout = self.create_pango_layout(self._text)
        layout.set_font_description(self._font)
        layout.set_single_paragraph_mode(True)
        self._text_width, self._text_height = layout.get_pixel_size()
        self.set_content_height(max(18, self._text_height + 2))

    def _on_map(self, *_args):
        self._measure_text()
        self._sync_animation()

    def _on_unmap(self, *_args):
        self._stop_tick()

    def _sync_animation(self):
        width = self.get_width()
        needs_scroll = bool(self._text) and self._text_width > width + 4
        if self._active and needs_scroll and self.get_mapped():
            self._start_tick()
        else:
            self._stop_tick()

    def _start_tick(self):
        if self._tick_id is None:
            self._last_frame_time = 0
            self._tick_id = self.add_tick_callback(self._on_frame_tick)

    def _stop_tick(self):
        if self._tick_id is not None:
            self.remove_tick_callback(self._tick_id)
            self._tick_id = None
            self._last_frame_time = 0

    def _on_frame_tick(self, _widget, frame_clock):
        if not self._active or not self.get_mapped():
            self._tick_id = None
            return GLib.SOURCE_REMOVE

        width = self.get_width()
        if self._text_width <= width + 4:
            self._tick_id = None
            return GLib.SOURCE_REMOVE

        frame_time = frame_clock.get_frame_time()
        if self._last_frame_time == 0:
            self._last_frame_time = frame_time
            return GLib.SOURCE_CONTINUE

        dt = (frame_time - self._last_frame_time) / 1_000_000.0
        self._last_frame_time = frame_time

        # Bound dt to prevent huge jump on wake/lag
        dt = min(0.1, max(0.001, dt))
        cycle = self._text_width + self.gap
        if cycle > 0:
            self._offset = (self._offset + self.speed * dt) % cycle
            self.queue_draw()

        return GLib.SOURCE_CONTINUE

    def _draw(self, _area, cr, width, height):
        if not self._text or width <= 1 or height <= 1:
            return

        # Dynamically trigger tick if width was newly allocated
        needs_scroll = self._text_width > width + 4
        if (
            self._active
            and needs_scroll
            and self._tick_id is None
            and self.get_mapped()
        ):
            self._start_tick()
        elif not self._active and self._tick_id is not None:
            self._stop_tick()

        layout = self.create_pango_layout(self._text)
        layout.set_font_description(self._font)
        layout.set_single_paragraph_mode(True)

        # Style color
        style = self.get_style_context()
        color = style.get_color()
        y = max(0, (height - self._text_height) / 2.0)

        cr.save()
        cr.rectangle(0, 0, width, height)
        cr.clip()

        if not needs_scroll:
            # Fits perfectly, draw centered/left aligned
            cr.set_source_rgba(color.red, color.green, color.blue, color.alpha)
            cr.move_to(0, y)
            PangoCairo.show_layout(cr, layout)
            cr.restore()
            return

        if not self._active:
            # Inactive overflowing: render static with right edge fade mask
            cr.push_group()
            cr.set_source_rgba(color.red, color.green, color.blue, color.alpha)
            cr.move_to(0, y)
            PangoCairo.show_layout(cr, layout)
            text_surf = cr.pop_group()

            # Create soft right edge fade mask
            fade_w = min(24.0, width * 0.2)
            mask = cairo.LinearGradient(width - fade_w, 0, width, 0)
            mask.add_color_stop_rgba(0.0, 0, 0, 0, 1.0)
            mask.add_color_stop_rgba(1.0, 0, 0, 0, 0.0)

            cr.set_source(text_surf)
            cr.mask(mask)
            cr.restore()
            return

        # Active scrolling marquee
        cr.push_group()
        cr.set_source_rgba(color.red, color.green, color.blue, color.alpha)

        cycle = self._text_width + self.gap
        x = -self._offset
        while x < width:
            cr.move_to(x, y)
            PangoCairo.show_layout(cr, layout)
            x += cycle

        text_surf = cr.pop_group()

        # Soft fades at both left and right edges for smooth loop
        fade_w = min(18.0, width * 0.15)
        mask = cairo.LinearGradient(0, 0, width, 0)
        mask.add_color_stop_rgba(0.0, 0, 0, 0, 0.0)
        mask.add_color_stop_rgba(fade_w / width, 0, 0, 0, 1.0)
        mask.add_color_stop_rgba(1.0 - (fade_w / width), 0, 0, 0, 1.0)
        mask.add_color_stop_rgba(1.0, 0, 0, 0, 0.0)

        cr.set_source(text_surf)
        cr.mask(mask)
        cr.restore()


class MarqueeLabel:
    def __init__(self, scrolled_window: Gtk.ScrolledWindow, label: Gtk.Label, **kwargs):
        self.scrolled = scrolled_window
        self.label = label
        self.canvas = MarqueeDrawingArea(**kwargs)

        self.scrolled.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.NEVER)
        self.scrolled.set_propagate_natural_width(False)
        self.scrolled.set_propagate_natural_height(True)
        self.scrolled.set_hexpand(True)
        self.scrolled.set_halign(Gtk.Align.FILL)
        self.scrolled.set_size_request(1, -1)
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
