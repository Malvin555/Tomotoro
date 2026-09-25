import math
import random

import cairo
from gi.repository import Adw, GLib, Gtk


class LiveStatViz(Gtk.DrawingArea):
    """Subtle, modern live data visualization for Focus Time & Completed stat cards.

    Uses GTK4 frame clock callbacks for smooth 60fps native Cairo rendering with
    dynamic Adwaita accent colors and zero overhead when idle.
    """

    def __init__(self, mode: str = "sessions", **kwargs):
        super().__init__(**kwargs)
        self.mode = mode
        self.value = 0.0
        self.active = False
        self._phase = random.uniform(0, 2 * math.pi)
        self._tick_id = None
        self._last_frame_time = 0

        self._point_count = 16
        self._points = [
            0.35 + 0.15 * math.sin(i * 0.6) for i in range(self._point_count)
        ]

        self.set_content_width(1)
        self.set_content_height(34)
        self.set_size_request(1, 34)
        self.set_hexpand(True)
        self.set_halign(Gtk.Align.FILL)
        self.set_draw_func(self._draw)
        self.add_css_class("stat-viz")

        self.connect("map", self._on_map)
        self.connect("unmap", self._on_unmap)

    def set_active(self, active: bool):
        active = bool(active)
        if active == self.active:
            return
        self.active = active
        if self.active:
            self._ensure_tick()
        else:
            self._stop_tick()
        self.queue_draw()

    def set_value(self, value: float):
        self.value = max(0.0, float(value))
        self.queue_draw()

    def _on_map(self, *_args):
        if self.active:
            self._ensure_tick()

    def _on_unmap(self, *_args):
        self._stop_tick()

    def _ensure_tick(self):
        if self._tick_id is None and self.get_mapped() and self.active:
            self._last_frame_time = 0
            self._tick_id = self.add_tick_callback(self._on_tick)

    def _stop_tick(self):
        if self._tick_id is not None:
            self.remove_tick_callback(self._tick_id)
            self._tick_id = None
            self._last_frame_time = 0

    def _on_tick(self, _widget, frame_clock):
        if not self.active or not self.get_mapped():
            self._tick_id = None
            return GLib.SOURCE_REMOVE

        frame_time = frame_clock.get_frame_time()
        if self._last_frame_time == 0:
            self._last_frame_time = frame_time
            return GLib.SOURCE_CONTINUE

        dt = (frame_time - self._last_frame_time) / 1_000_000.0
        self._last_frame_time = frame_time
        dt = min(0.1, max(0.001, dt))

        self._phase = (self._phase + 2.2 * dt) % (2 * math.pi)

        if self.mode == "focus":
            target_level = min(0.65, 0.25 + (self.value / 7200.0) * 0.35)
            for i in range(self._point_count):
                wave = math.sin(self._phase + i * 0.55) * 0.18
                micro = math.sin(self._phase * 1.6 + i * 0.8) * 0.08
                desired = target_level + wave + micro
                desired = max(0.12, min(0.88, desired))
                self._points[i] += (desired - self._points[i]) * min(1.0, 6.0 * dt)

        self.queue_draw()
        return GLib.SOURCE_CONTINUE

    def _accent_color(self):
        try:
            rgba = Adw.StyleManager.get_default().get_accent_color_rgba()
            return rgba.red, rgba.green, rgba.blue
        except Exception:
            return 0.35, 0.45, 0.95

    def _draw(self, _area, cr, width, height):
        if width <= 1 or height <= 1:
            return

        r, g, b = self._accent_color()

        if self.mode == "sessions":
            self._draw_sessions(cr, width, height, r, g, b)
        else:
            self._draw_focus_wave(cr, width, height, r, g, b)

    def _draw_sessions(self, cr, width, height, r, g, b):
        """Draws a refined milestone bar matrix with live breathing pulse."""
        bar_count = 8
        gap = 4.0
        bar_w = max(4.0, (width - gap * (bar_count - 1)) / bar_count)
        completed = int(self.value)
        active_index = completed % bar_count

        for i in range(bar_count):
            x = i * (bar_w + gap)
            is_completed = (i < completed) or (completed >= bar_count and i < bar_count)
            is_active_now = (i == active_index) and self.active

            if is_completed:
                level = 0.85
                alpha = 0.75
            elif is_active_now:
                pulse = 0.45 + 0.35 * (0.5 + 0.5 * math.sin(self._phase * 2.0))
                level = pulse
                alpha = 0.45 + 0.35 * pulse
            else:
                level = 0.22
                alpha = 0.12

            bar_h = max(4.0, height * level)
            y = height - bar_h
            radius = min(3.0, bar_w / 2.0)

            cr.new_sub_path()
            cr.arc(x + radius, y + radius, radius, math.pi, math.pi * 1.5)
            cr.arc(x + bar_w - radius, y + radius, radius, math.pi * 1.5, 0)
            cr.arc(x + bar_w - radius, height - radius, radius, 0, math.pi * 0.5)
            cr.arc(x + radius, height - radius, radius, math.pi * 0.5, math.pi)
            cr.close_path()

            cr.set_source_rgba(r, g, b, alpha)
            cr.fill()

            if is_active_now:
                glow_r = min(3.5, bar_w / 2.0)
                cr.arc(x + bar_w / 2.0, y - 2.0, glow_r, 0, 2 * math.pi)
                cr.set_source_rgba(r, g, b, 0.85)
                cr.fill()

    def _draw_focus_wave(self, cr, width, height, r, g, b):
        """Draws a smooth organic bezier stream wave with subtle gradient glow."""
        if len(self._points) < 3:
            return

        step = width / (len(self._points) - 1)
        pts = [
            (i * step, height - self._points[i] * height)
            for i in range(len(self._points))
        ]

        cr.save()
        cr.move_to(0, height)
        cr.line_to(pts[0][0], pts[0][1])

        for i in range(len(pts) - 1):
            p0 = pts[i]
            p1 = pts[i + 1]
            mid_x = (p0[0] + p1[0]) / 2.0
            mid_y = (p0[1] + p1[1]) / 2.0
            cr.curve_to(mid_x, p0[1], mid_x, p1[1], p1[0], p1[1])

        cr.line_to(width, height)
        cr.close_path()

        fill_alpha = 0.28 if self.active else 0.14
        grad = cairo.LinearGradient(0, 0, 0, height)
        grad.add_color_stop_rgba(0.0, r, g, b, fill_alpha)
        grad.add_color_stop_rgba(1.0, r, g, b, 0.02)
        cr.set_source(grad)
        cr.fill()
        cr.restore()

        cr.save()
        cr.move_to(pts[0][0], pts[0][1])
        for i in range(len(pts) - 1):
            p0 = pts[i]
            p1 = pts[i + 1]
            mid_x = (p0[0] + p1[0]) / 2.0
            mid_y = (p0[1] + p1[1]) / 2.0
            cr.curve_to(mid_x, p0[1], mid_x, p1[1], p1[0], p1[1])

        stroke_alpha = 0.80 if self.active else 0.35
        cr.set_line_width(1.8)
        cr.set_line_cap(cairo.LINE_CAP_ROUND)
        cr.set_source_rgba(r, g, b, stroke_alpha)
        cr.stroke()
        cr.restore()
