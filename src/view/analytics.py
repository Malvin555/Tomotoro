from gi.repository import Adw, Gtk

from ..services.analytics import AnalyticsService


class WeeklyBarChart(Gtk.DrawingArea):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.data = []
        self.set_draw_func(self._draw)
        self.set_size_request(-1, 140)
        self.set_hexpand(True)
        self.set_vexpand(True)

    def set_data(self, data):
        self.data = data
        self.queue_draw()

    def _draw(self, area, cr, width, height):
        if not self.data:
            return

        accent = (0.38, 0.42, 0.95)
        try:
            rgba = Adw.StyleManager.get_default().get_accent_color_rgba()
            accent = (rgba.red, rgba.green, rgba.blue)
        except Exception:
            pass  # libadwaita < 1.6 — fall back to the default tone above

        padding_bottom = 22
        chart_height = height - padding_bottom
        max_value = max((m for _, m in self.data), default=0) or 1
        gap = 10
        bar_count = len(self.data)
        bar_width = (width - gap * (bar_count - 1)) / bar_count

        cr.select_font_face("Sans")
        cr.set_font_size(11)

        for i, (label, minutes) in enumerate(self.data):
            x = i * (bar_width + gap)
            bar_height = (minutes / max_value) * (chart_height - 10)
            y = chart_height - bar_height
            radius = min(6, bar_width / 2)

            cr.new_sub_path()
            cr.arc(x + radius, y + radius, radius, 3.14159, 3.14159 * 1.5)
            cr.arc(x + bar_width - radius, y + radius, radius, 3.14159 * 1.5, 0)
            cr.line_to(x + bar_width, chart_height)
            cr.line_to(x, chart_height)
            cr.close_path()

            if minutes > 0:
                cr.set_source_rgba(*accent, 0.9)
            else:
                cr.set_source_rgba(0, 0, 0, 0.08)
            cr.fill()

            cr.set_source_rgba(0.5, 0.5, 0.5, 0.8)
            extents = cr.text_extents(label)
            cr.move_to(x + bar_width / 2 - extents.width / 2, height - 6)
            cr.show_text(label)


@Gtk.Template(resource_path="/org/maldoro/fyvin/analytics.ui")
class AnalyticsView(Gtk.Box):
    __gtype_name__ = "AnalyticsView"

    total_sessions_value = Gtk.Template.Child()
    total_focus_value = Gtk.Template.Child()
    streak_value = Gtk.Template.Child()
    most_played_value = Gtk.Template.Child()
    most_played_count = Gtk.Template.Child()
    chart_container = Gtk.Template.Child()

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.analytics_service = AnalyticsService.get_default()
        self.analytics_service.on_change_callbacks.append(self._refresh)

        self.chart = WeeklyBarChart()
        self.chart_container.append(self.chart)

        self._refresh()

    def _refresh(self):
        hours, minutes = self.analytics_service.get_total_focus_hours_minutes()
        self.total_focus_value.set_label(f"{hours}h {minutes}m")
        self.total_sessions_value.set_label(str(self.analytics_service.total_sessions))
        self.streak_value.set_label(f"{self.analytics_service.get_current_streak()}d")

        track_name, count = self.analytics_service.get_most_played_track()
        self.most_played_value.set_label(track_name or "—")
        self.most_played_count.set_label(f"{count} plays" if count else "No plays yet")

        self.chart.set_data(self.analytics_service.get_last_7_days())
