import math
import random

from gi.repository import Adw, GLib, Gtk


class LiveStatViz(Gtk.DrawingArea):
    """Lightweight animated background for Completed / Focus Time cards."""

    def __init__(self, mode: str = "sessions", **kwargs):
        super().__init__(**kwargs)
        self.mode = mode  # "sessions" | "focus"
        self.value = 0.0
        self.active = False
        self._phase = random.uniform(0, 2 * math.pi)
        self._tick_id = None
        self._points = [random.uniform(0.2, 0.55) for _ in range(18)]

        self.set_content_width(120)
        self.set_content_height(36)
        self.set_hexpand(True)
        self.set_draw_func(self._draw)
        self.add_css_class("stat-viz")

        self.connect("map", self._on_map)
        self.connect("unmap", self._on_unmap)

    def set_active(self, active: bool):
        self.active = bool(active)
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
            self._tick_id = GLib.timeout_add(40, self._on_tick)

    def _stop_tick(self):
        if self._tick_id is not None:
            GLib.source_remove(self._tick_id)
            self._tick_id = None

    def _on_tick(self):
        if not self.active:
            self._tick_id = None
            return False

        self._phase += 0.08
        if self.mode == "focus":
            drift = 0.04
            target = 0.25 + min(0.55, self.value / 3600.0)
            target += 0.12 * math.sin(self._phase * 1.7)
            self._points.pop(0)
            last = self._points[-1]
            nxt = last + (target - last) * 0.18 + random.uniform(-drift, drift)
            self._points.append(max(0.08, min(0.92, nxt)))
        self.queue_draw()
        return True

    def _accent(self):
        try:
            rgba = Adw.StyleManager.get_default().get_accent_color_rgba()
            return rgba.red, rgba.green, rgba.blue
        except Exception:
            return 0.38, 0.42, 0.95

    def _draw(self, _area, cr, width, height):
        if width <= 1 or height <= 1:
            return

        accent = self._accent()
        base_alpha = 0.18 if self.active else 0.10

        if self.mode == "sessions":
            self._draw_sessions(cr, width, height, accent, base_alpha)
        else:
            self._draw_focus(cr, width, height, accent, base_alpha)

    def _draw_sessions(self, cr, width, height, accent, base_alpha):
        # Soft activity bars that pulse with completed progress.
        bars = 7
        gap = 4
        bar_w = max(3.0, (width - gap * (bars - 1)) / bars)
        completed = int(self.value)
        for i in range(bars):
            wave = 0.45 + 0.35 * math.sin(self._phase + i * 0.7)
            if i < completed % bars or (completed > 0 and i < min(bars, completed)):
                level = 0.35 + 0.55 * wave
                alpha = base_alpha + 0.22
            else:
                level = 0.18 + 0.12 * wave
                alpha = base_alpha
            bar_h = height * level
            x = i * (bar_w + gap)
            y = height - bar_h
            radius = min(3.0, bar_w / 2)
            cr.new_sub_path()
            cr.arc(x + radius, y + radius, radius, math.pi, math.pi * 1.5)
            cr.arc(x + bar_w - radius, y + radius, radius, math.pi * 1.5, 0)
            cr.line_to(x + bar_w, height)
            cr.line_to(x, height)
            cr.close_path()
            cr.set_source_rgba(*accent, alpha)
            cr.fill()

    def _draw_focus(self, cr, width, height, accent, base_alpha):
        # Minimal sparkline / waveform.
        if len(self._points) < 2:
            return

        step = width / (len(self._points) - 1)

        # Fill under the line for a gentle “live data” feel.
        cr.move_to(0, height)
        cr.line_to(0, height - self._points[0] * height)
        for i, p in enumerate(self._points[1:], start=1):
            cr.line_to(i * step, height - p * height)
        cr.line_to(width, height)
        cr.close_path()
        cr.set_source_rgba(*accent, base_alpha * 0.55)
        cr.fill()

        cr.set_line_width(1.6)
        cr.set_source_rgba(*accent, base_alpha + 0.28)
        cr.move_to(0, height - self._points[0] * height)
        for i, p in enumerate(self._points[1:], start=1):
            cr.line_to(i * step, height - p * height)
        cr.stroke()
