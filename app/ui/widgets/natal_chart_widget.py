from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING

from PySide6.QtCore import QByteArray, QPointF, QRectF, Qt
from PySide6.QtGui import (
    QColor,
    QFont,
    QFontMetricsF,
    QImage,
    QPainter,
    QPainterPath,
    QPaintEvent,
    QPen,
)
from PySide6.QtWidgets import QWidget

from app.models.chart import Chart
from app.models.planet_position import PlanetPosition
from app.ui.widgets.chart_geometry import (
    ChartGeometry,
    OuterWheelGeometry,
    point_on_circle,
)
from app.utils.angle_utils import normalize_angle, shortest_angular_distance

if TYPE_CHECKING:
    from PySide6.QtSvg import QSvgRenderer

SIGN_ABBREVIATIONS = (
    'Ar', 'Ta', 'Ge', 'Cn', 'Le', 'Vi', 'Li', 'Sc', 'Sg', 'Cp', 'Aq', 'Pi'
)
SIGN_GLYPHS = {
    'Ar': '\u2648',
    'Ta': '\u2649',
    'Ge': '\u264A',
    'Cn': '\u264B',
    'Le': '\u264C',
    'Vi': '\u264D',
    'Li': '\u264E',
    'Sc': '\u264F',
    'Sg': '\u2650',
    'Cp': '\u2651',
    'Aq': '\u2652',
    'Pi': '\u2653',
}
SIGN_ASSET_IDS = (
    'Ari', 'Tau', 'Gem', 'Can', 'Leo', 'Vir', 'Lib', 'Sco', 'Sag', 'Cap', 'Aqu', 'Pis'
)
PLANET_ASSET_IDS = {
    'Sun': 'Sun',
    'Moon': 'Moon',
    'Mercury': 'Mercury',
    'Venus': 'Venus',
    'Mars': 'Mars',
    'Jupiter': 'Jupiter',
    'Saturn': 'Saturn',
    'Uranus': 'Uranus',
    'Neptune': 'Neptune',
    'Pluto': 'Pluto',
    'Node': 'Mean_North_Lunar_Node',
    'North Node': 'Mean_North_Lunar_Node',
    'South Node': 'Mean_South_Lunar_Node',
    'Chiron': 'Chiron',
    'Lilith': 'Mean_Lilith',
    'Fortune': 'Pars_Fortunae',
    'Vertex': 'Vertex',
}

SIGN_COLORS = {
    'Ar': QColor('#ff3c2f'),
    'Ta': QColor('#63a51d'),
    'Ge': QColor('#f39c12'),
    'Cn': QColor('#2954ea'),
    'Le': QColor('#ff302a'),
    'Vi': QColor('#4f9d1d'),
    'Li': QColor('#f39c12'),
    'Sc': QColor('#204bdf'),
    'Sg': QColor('#ff5722'),
    'Cp': QColor('#5f8d17'),
    'Aq': QColor('#f39c12'),
    'Pi': QColor('#2962ff'),
}

PLANET_LABELS = {
    'Sun': '\u2609',
    'Moon': '\u263D',
    'Mercury': '\u263F',
    'Venus': '\u2640',
    'Mars': '\u2642',
    'Jupiter': '\u2643',
    'Saturn': '\u2644',
    'Uranus': '\u2645',
    'Neptune': '\u2646',
    'Pluto': '\u2647',
    'Node': '\u260A',
    'North Node': '\u260A',
    'South Node': '\u260B',
    'Chiron': '\u26B7',
    'Lilith': 'Li',
    'Fortune': '\u2297',
    'Vertex': 'Vx',
}

TRANSIT_ABBREVIATIONS = {
    'Sun': 'Su',
    'Moon': 'Mo',
    'Mercury': 'Me',
    'Venus': 'Ve',
    'Mars': 'Ma',
    'Jupiter': 'Ju',
    'Saturn': 'Sa',
    'Uranus': 'Ur',
    'Neptune': 'Ne',
    'Pluto': 'Pl',
}

HARD_ASPECTS = {'square', 'opposition'}
SOFT_ASPECTS = {'trine', 'sextile'}


@dataclass(frozen=True)
class PlanetGlyphLayout:
    position: PlanetPosition
    cluster_index: int
    cluster_size: int
    cluster_longitude: float
    base_anchor: QPointF
    glyph_center: QPointF
    connector_start: QPointF
    connector_end: QPointF


class NatalChartWidget(QWidget):
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._chart: Chart | None = None
        self._transit_positions = []
        self._debug_overlay_enabled = False
        self._svg_cache: dict[tuple[str, str], object] = {}
        self._use_svg_symbols = not self._prefer_text_symbol_fallback()
        self.setObjectName('natalChartWheel')
        self.setMinimumHeight(560)

    @property
    def chart(self) -> Chart | None:
        return self._chart

    def set_chart(self, chart: Chart | None) -> None:
        self._chart = chart
        if chart is None:
            self._transit_positions = []
        self.update()

    def set_transit_positions(self, positions: list) -> None:
        self._transit_positions = list(positions)
        self.update()

    def set_debug_overlay_enabled(self, enabled: bool) -> None:
        self._debug_overlay_enabled = enabled
        self.update()

    def export_png(self, path: Path) -> bool:
        image = QImage(self.size(), QImage.Format.Format_ARGB32)
        image.fill(QColor('#fffdfa'))
        painter = QPainter(image)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        self._paint_chart(painter)
        painter.end()
        return image.save(str(path), 'PNG')

    def paintEvent(self, event: QPaintEvent) -> None:
        del event
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        self._paint_chart(painter)

    def _paint_chart(self, painter: QPainter) -> None:
        painter.fillRect(self.rect(), QColor('#fffdfa'))
        if self._chart is None or not self._chart.house_cusps:
            self._draw_empty_state(painter)
            return

        outer_padding = 140 if self._transit_positions else 110
        side = min(self.width(), self.height()) - outer_padding
        outer_radius = side / 2
        center = QPointF(self.width() / 2, self.height() / 2)

        geometry = ChartGeometry.from_outer_radius(outer_radius)
        outer_wheel = geometry.outer_wheel
        zodiac_inner_radius = outer_wheel.inner_border_radius
        house_outer_radius = geometry.house_outer_radius
        house_inner_radius = geometry.house_inner_radius
        planet_line_radius = geometry.planet_band_outer_radius
        planet_ring_radius = geometry.planet_ring_radius

        ascendant = normalize_angle(self._chart.ascendant or self._chart.house_cusps[0].longitude)

        self._draw_outer_rings(
            painter,
            center,
            outer_wheel,
            house_outer_radius,
            house_inner_radius,
        )
        self._draw_degree_ticks(painter, center, outer_wheel, ascendant)
        self._draw_sign_boundaries(
            painter,
            center,
            outer_wheel.outer_border_radius,
            zodiac_inner_radius,
            ascendant,
        )
        self._draw_sign_labels(painter, center, outer_wheel, ascendant)
        self._draw_house_lines(
            painter,
            center,
            zodiac_inner_radius,
            geometry.aspect_radius,
            ascendant,
        )
        self._draw_house_numbers(
            painter,
            center,
            geometry,
            ascendant,
        )
        self._draw_cardinal_axes(
            painter,
            center,
            geometry,
            ascendant,
        )

        aspect_points = self._compute_aspect_anchors(
            center,
            geometry.aspect_radius,
            ascendant,
        )
        self._draw_aspects(painter, aspect_points)
        self._draw_planets(
            painter,
            center,
            planet_ring_radius,
            planet_line_radius,
            geometry.planet_band_inner_radius,
            ascendant,
        )
        self._draw_transit_positions(
            painter,
            center,
            geometry,
            ascendant,
        )
        if self._debug_overlay_enabled:
            self._draw_debug_overlay(painter, center, geometry, ascendant)

    def _draw_empty_state(self, painter: QPainter) -> None:
        painter.setPen(QPen(QColor('#8d877d'), 1))
        painter.drawText(
            self.rect(),
            Qt.AlignmentFlag.AlignCenter,
            'Calculate a natal chart to draw the wheel.',
        )

    def _draw_outer_rings(
        self,
        painter: QPainter,
        center: QPointF,
        outer_wheel: OuterWheelGeometry,
        house_outer_radius: float,
        house_inner_radius: float,
    ) -> None:
        painter.setBrush(QColor('#ffffff'))
        painter.setPen(QPen(QColor('#111111'), 2))
        painter.drawEllipse(
            center,
            outer_wheel.outer_border_radius,
            outer_wheel.outer_border_radius,
        )

        # Keep the zodiac label band visually clear from the degree tick band.
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QColor('#fffdfa'))
        painter.drawEllipse(
            center,
            outer_wheel.zodiac_label_band_outer_radius,
            outer_wheel.zodiac_label_band_outer_radius,
        )
        painter.setBrush(QColor('#ffffff'))
        painter.drawEllipse(
            center,
            outer_wheel.zodiac_label_band_inner_radius,
            outer_wheel.zodiac_label_band_inner_radius,
        )

        painter.setPen(QPen(QColor('#111111'), 1.2))
        painter.setBrush(Qt.BrushStyle.NoBrush)
        painter.drawEllipse(
            center,
            outer_wheel.inner_border_radius,
            outer_wheel.inner_border_radius,
        )

        painter.setPen(QPen(QColor('#111111'), 1.1))
        painter.drawEllipse(center, house_outer_radius, house_outer_radius)

        painter.setPen(QPen(QColor('#111111'), 1.0))
        painter.drawEllipse(center, house_inner_radius, house_inner_radius)

    def _draw_degree_ticks(
        self,
        painter: QPainter,
        center: QPointF,
        outer_wheel: OuterWheelGeometry,
        ascendant: float,
    ) -> None:
        tick_outer_radius = outer_wheel.tick_outer_radius
        zodiac_label_limit = outer_wheel.zodiac_label_limit
        for degree in range(360):
            if degree % 10 == 0:
                tick_inner_radius = outer_wheel.tick_inner_radius_10
                width = 1.2
                color = QColor('#111111')
            elif degree % 5 == 0:
                tick_inner_radius = outer_wheel.tick_inner_radius_5
                width = 0.95
                color = QColor('#363636')
            else:
                tick_inner_radius = outer_wheel.tick_inner_radius_1
                width = 0.6
                color = QColor('#9f9f9f')
            tick_inner_radius = min(tick_inner_radius, tick_outer_radius)
            tick_inner_radius = max(tick_inner_radius, zodiac_label_limit)
            start = point_on_circle(
                center,
                tick_outer_radius,
                float(degree),
                ascendant,
            )
            end = point_on_circle(
                center,
                tick_inner_radius,
                float(degree),
                ascendant,
            )
            painter.setPen(QPen(color, width))
            painter.drawLine(start, end)

    def _draw_sign_boundaries(
        self,
        painter: QPainter,
        center: QPointF,
        outer_radius: float,
        inner_radius: float,
        ascendant: float,
    ) -> None:
        for sign_index in range(12):
            longitude = sign_index * 30.0
            start = point_on_circle(center, outer_radius, longitude, ascendant)
            end = point_on_circle(center, inner_radius, longitude, ascendant)
            painter.setPen(QPen(QColor('#111111'), 1.2))
            painter.drawLine(start, end)

    def _draw_sign_labels(
        self,
        painter: QPainter,
        center: QPointF,
        outer_wheel,
        ascendant: float,
    ) -> None:
        sign_size = 22.0
        sign_pairs = zip(SIGN_ABBREVIATIONS, SIGN_ASSET_IDS, strict=True)
        for sign_index, (label, asset_id) in enumerate(sign_pairs):
            longitude = sign_index * 30.0 + 15.0
            point = point_on_circle(
                center,
                outer_wheel.zodiac_glyph_outer_radius,
                longitude,
                ascendant,
            )
            rect = QRectF(
                point.x() - (sign_size / 2),
                point.y() - (sign_size / 2),
                sign_size,
                sign_size,
            )
            renderer = self._get_svg_renderer(asset_id, SIGN_COLORS[label])
            if renderer is not None:
                renderer.render(painter, rect)
                continue
            painter.setPen(QPen(SIGN_COLORS[label], 1.0))
            fallback_font = QFont('Segoe UI Symbol', 16)
            painter.setFont(fallback_font)
            painter.drawText(rect, Qt.AlignmentFlag.AlignCenter, SIGN_GLYPHS[label])

    def _sign_label_rects(
        self,
        center: QPointF,
        outer_wheel: OuterWheelGeometry,
        ascendant: float,
    ) -> list[QRectF]:
        sign_size = 22.0
        rects: list[QRectF] = []
        for sign_index in range(12):
            longitude = sign_index * 30.0 + 15.0
            point = point_on_circle(
                center,
                outer_wheel.zodiac_glyph_outer_radius,
                longitude,
                ascendant,
            )
            rects.append(
                QRectF(
                    point.x() - (sign_size / 2),
                    point.y() - (sign_size / 2),
                    sign_size,
                    sign_size,
                )
            )
        return rects

    @staticmethod
    def _prefer_text_symbol_fallback() -> bool:
        return (
            os.environ.get('QT_QPA_PLATFORM') == 'offscreen'
            or os.environ.get('CI', '').lower() == 'true'
        )

    def _get_svg_renderer(self, asset_id: str, color: QColor) -> QSvgRenderer | None:
        if not self._use_svg_symbols:
            return None
        cache_key = (asset_id, color.name())
        renderer = self._svg_cache.get(cache_key)
        if renderer is not None:
            return renderer

        from PySide6.QtSvg import QSvgRenderer

        from app.ui.widgets.astrology_symbol_loader import build_symbol_svg

        svg = build_symbol_svg(asset_id, color.name())
        renderer = QSvgRenderer(QByteArray(svg.encode('utf-8')), self)
        self._svg_cache[cache_key] = renderer
        return renderer

    def _draw_house_lines(
        self,
        painter: QPainter,
        center: QPointF,
        zodiac_inner_radius: float,
        aspect_radius: float,
        ascendant: float,
    ) -> None:
        for cusp in self._chart.house_cusps:
            if cusp.house_number in {1, 4, 7, 10}:
                continue
            start = point_on_circle(center, zodiac_inner_radius, cusp.longitude, ascendant)
            end = point_on_circle(center, aspect_radius, cusp.longitude, ascendant)
            painter.setPen(QPen(QColor('#8b8b8b'), 0.9))
            painter.drawLine(start, end)

    def _draw_house_numbers(
        self,
        painter: QPainter,
        center: QPointF,
        geometry: ChartGeometry,
        ascendant: float,
    ) -> None:
        house_font = QFont('Times New Roman', 9)
        painter.setFont(house_font)
        painter.setPen(QPen(QColor('#222222'), 0.9))
        house_cusps = sorted(self._chart.house_cusps, key=lambda cusp: cusp.house_number)
        for index, cusp in enumerate(house_cusps):
            next_cusp = house_cusps[(index + 1) % len(house_cusps)]
            midpoint = self._circular_midpoint(cusp.longitude, next_cusp.longitude)
            point = point_on_circle(
                center,
                geometry.house_number_radius,
                midpoint,
                ascendant,
            )
            marker_radius = geometry.house_number_marker_radius
            marker_rect = QRectF(
                point.x() - marker_radius,
                point.y() - marker_radius,
                marker_radius * 2,
                marker_radius * 2,
            )
            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(QColor('#fffdfa'))
            painter.drawEllipse(marker_rect)
            painter.setPen(QPen(QColor('#c6c6c6'), 0.9))
            painter.setBrush(Qt.BrushStyle.NoBrush)
            painter.drawEllipse(marker_rect)
            rect = QRectF(point.x() - 10, point.y() - 10, 20, 20)
            painter.setPen(QPen(QColor('#222222'), 0.9))
            painter.drawText(rect, Qt.AlignmentFlag.AlignCenter, str(cusp.house_number))

    def _draw_cardinal_axes(
        self,
        painter: QPainter,
        center: QPointF,
        geometry: ChartGeometry,
        ascendant: float,
    ) -> None:
        cardinal_points = {
            'ASC': normalize_angle(ascendant),
            'DSC': normalize_angle(ascendant + 180.0),
            'MC': normalize_angle(self._chart.midheaven or ascendant + 90.0),
            'IC': normalize_angle((self._chart.midheaven or ascendant + 90.0) + 180.0),
        }
        axis_font = QFont('Arial', 8)
        axis_font.setBold(True)
        for label, longitude in cardinal_points.items():
            thick_start = point_on_circle(
                center,
                geometry.cardinal_axis_outer_radius,
                longitude,
                ascendant,
            )
            thick_end = point_on_circle(
                center,
                geometry.cardinal_axis_inner_radius,
                longitude,
                ascendant,
            )
            thin_end = point_on_circle(
                center,
                geometry.aspect_radius,
                longitude,
                ascendant,
            )
            painter.setPen(QPen(QColor('#111111'), 3.2))
            painter.drawLine(thick_start, thick_end)
            painter.setPen(QPen(QColor('#8b8b8b'), 0.95))
            painter.drawLine(thick_end, thin_end)

            text_point = point_on_circle(
                center,
                geometry.cardinal_axis_label_radius,
                longitude,
                ascendant,
            )
            painter.setFont(axis_font)
            painter.setPen(QPen(QColor('#111111'), 1))
            metrics = QFontMetricsF(axis_font)
            label_width = metrics.horizontalAdvance(label) + 6
            label_height = metrics.height()
            text_rect = QRectF(
                text_point.x() - (label_width / 2),
                text_point.y() - (label_height / 2),
                label_width,
                label_height,
            )
            painter.drawText(text_rect, Qt.AlignmentFlag.AlignCenter, label)

    def _cardinal_label_rects(
        self,
        center: QPointF,
        geometry: ChartGeometry,
        ascendant: float,
    ) -> list[QRectF]:
        cardinal_points = {
            'ASC': normalize_angle(ascendant),
            'DSC': normalize_angle(ascendant + 180.0),
            'MC': normalize_angle(self._chart.midheaven or ascendant + 90.0),
            'IC': normalize_angle((self._chart.midheaven or ascendant + 90.0) + 180.0),
        }
        axis_font = QFont('Arial', 8)
        axis_font.setBold(True)
        metrics = QFontMetricsF(axis_font)
        rects: list[QRectF] = []
        for label, longitude in cardinal_points.items():
            text_point = point_on_circle(
                center,
                geometry.cardinal_axis_label_radius,
                longitude,
                ascendant,
            )
            label_width = metrics.horizontalAdvance(label) + 6
            label_height = metrics.height()
            rects.append(
                QRectF(
                    text_point.x() - (label_width / 2),
                    text_point.y() - (label_height / 2),
                    label_width,
                    label_height,
                )
            )
        return rects

    def _draw_planets(
        self,
        painter: QPainter,
        center: QPointF,
        base_radius: float,
        leader_radius: float,
        planet_band_inner_radius: float,
        ascendant: float,
    ) -> None:
        glyph_font = QFont('Cambria Math', 22)
        glyph_font.setStyleStrategy(QFont.StyleStrategy.PreferAntialias)
        layouts = self._compute_planet_layouts(
            center,
            base_radius,
            leader_radius,
            planet_band_inner_radius,
            ascendant,
        )
        self._draw_planet_layouts(painter, layouts, glyph_font)

    def _compute_planet_layouts(
        self,
        center: QPointF,
        base_radius: float,
        leader_radius: float,
        planet_band_inner_radius: float,
        ascendant: float,
    ) -> list[PlanetGlyphLayout]:
        max_radius = base_radius
        glyph_draw_size = 20.0
        min_radius = planet_band_inner_radius + 4.0
        layouts: list[PlanetGlyphLayout] = []

        for sector in self._build_house_sectors():
            sector_positions = self._positions_in_sector(sector)
            if not sector_positions:
                continue
            for cluster in self._cluster_positions(sector_positions):
                cluster_size = len(cluster)
                cluster_longitude = self._cluster_angle(cluster)
                if cluster_size <= 1:
                    stack_step = 0.0
                else:
                    available_span = max(0.0, max_radius - min_radius)
                    stack_step = min(18.0, available_span / (cluster_size - 1))
                for index, position in enumerate(cluster):
                    glyph_radius = max(
                        min_radius,
                        min(max_radius, base_radius - index * stack_step),
                    )
                    base_anchor = point_on_circle(
                        center,
                        leader_radius,
                        position.longitude,
                        ascendant,
                    )
                    glyph_center = point_on_circle(
                        center,
                        glyph_radius,
                        cluster_longitude,
                        ascendant,
                    )
                    radial_dx = glyph_center.x() - base_anchor.x()
                    radial_dy = glyph_center.y() - base_anchor.y()
                    radial_length = (radial_dx**2 + radial_dy**2) ** 0.5
                    if radial_length <= 1e-6:
                        connector_start = glyph_center
                        connector_end = glyph_center
                    else:
                        glyph_edge_inset = glyph_draw_size * 0.45
                        glyph_edge_inset = min(glyph_edge_inset, radial_length)
                        connector_end = QPointF(
                            glyph_center.x() - (radial_dx / radial_length) * glyph_edge_inset,
                            glyph_center.y() - (radial_dy / radial_length) * glyph_edge_inset,
                        )
                        connector_start = base_anchor
                    layouts.append(
                        PlanetGlyphLayout(
                            position=position,
                            cluster_index=index,
                            cluster_size=cluster_size,
                            cluster_longitude=cluster_longitude,
                            base_anchor=base_anchor,
                            glyph_center=glyph_center,
                            connector_start=connector_start,
                            connector_end=connector_end,
                        )
                    )

        return layouts

    def _draw_planet_layouts(
        self,
        painter: QPainter,
        layouts: list[PlanetGlyphLayout],
        glyph_font: QFont,
    ) -> None:
        painter.setFont(glyph_font)
        glyph_metrics = QFontMetricsF(glyph_font)

        for layout in layouts:
            self._draw_planet_glyph(painter, layout, glyph_font, glyph_metrics)

    def _draw_planet_glyph(
        self,
        painter: QPainter,
        layout: PlanetGlyphLayout,
        glyph_font: QFont,
        glyph_metrics: QFontMetricsF,
    ) -> None:
        position = layout.position
        asset_id = PLANET_ASSET_IDS.get(position.body)
        if asset_id is not None:
            renderer = self._get_svg_renderer(asset_id, QColor('#111111'))
            if renderer is not None:
                glyph_size = 20.0
                glyph_rect = QRectF(
                    layout.glyph_center.x() - (glyph_size / 2),
                    layout.glyph_center.y() - (glyph_size / 2),
                    glyph_size,
                    glyph_size,
                )
                renderer.render(painter, glyph_rect)
                return

        glyph = PLANET_LABELS.get(position.body, position.body[:2])
        glyph_rect = glyph_metrics.tightBoundingRect(glyph)
        painter.setPen(QPen(QColor('#111111'), 1.1))
        painter.setFont(glyph_font)
        glyph_draw_rect = QRectF(
            layout.glyph_center.x() - (glyph_rect.width() / 2) - 1,
            layout.glyph_center.y() - (glyph_rect.height() / 2),
            glyph_rect.width() + 2,
            glyph_rect.height(),
        )
        painter.drawText(glyph_draw_rect, Qt.AlignmentFlag.AlignCenter, glyph)

    def _draw_aspects(self, painter: QPainter, placements: dict[str, QPointF]) -> None:
        self._draw_aspects_clipped(painter, placements)

    def _draw_aspects_clipped(self, painter: QPainter, placements: dict[str, QPointF]) -> None:
        if not placements:
            return
        center = QPointF(self.width() / 2, self.height() / 2)
        side = min(self.width(), self.height()) - 60
        geometry = ChartGeometry.from_outer_radius(side / 2)
        clip_path = QPainterPath()
        clip_path.addEllipse(center, geometry.aspect_radius, geometry.aspect_radius)
        painter.save()
        painter.setClipPath(clip_path)
        for aspect in self._chart.aspects:
            point_a = placements.get(aspect.body_a)
            point_b = placements.get(aspect.body_b)
            if point_a is None or point_b is None:
                continue
            pen = self._aspect_pen(aspect.aspect_type)
            painter.setPen(pen)
            painter.drawLine(point_a, point_b)
        painter.restore()

    @staticmethod
    def _aspect_pen(aspect_type: str) -> QPen:
        aspect_name = aspect_type.lower()
        if aspect_name in HARD_ASPECTS:
            return QPen(QColor('#e0453a'), 1.05)
        if aspect_name in SOFT_ASPECTS:
            return QPen(QColor('#2f63f0'), 1.05)
        if aspect_name == 'conjunction':
            pen = QPen(QColor('#8c8c8c'), 0.9)
            pen.setStyle(Qt.PenStyle.DotLine)
            return pen
        pen = QPen(QColor('#9a9a9a'), 0.85)
        pen.setStyle(Qt.PenStyle.DashLine)
        return pen

    def _compute_aspect_anchors(
        self,
        center: QPointF,
        aspect_radius: float,
        ascendant: float,
    ) -> dict[str, QPointF]:
        return {
            position.body: point_on_circle(
                center,
                aspect_radius,
                position.longitude,
                ascendant,
            )
            for position in self._chart.planet_positions
        }

    def _draw_transit_positions(
        self,
        painter: QPainter,
        center: QPointF,
        geometry: ChartGeometry,
        ascendant: float,
    ) -> None:
        if not self._transit_positions:
            return
        font = QFont('Arial', 8)
        painter.setFont(font)
        metrics = QFontMetricsF(font)
        content_rect = QRectF(self.rect()).adjusted(8, 8, -8, -8)
        forbidden_rects = [
            rect.adjusted(-4, -4, 4, 4)
            for rect in self._sign_label_rects(center, geometry.outer_wheel, ascendant)
            + self._cardinal_label_rects(center, geometry, ascendant)
        ]
        accepted_rects: list[QRectF] = []
        painter.setPen(QPen(QColor('#c86a2b'), 1.0))
        painter.setBrush(QColor('#fff1e8'))

        sorted_positions = sorted(self._transit_positions, key=lambda item: item.longitude)
        clusters = self._cluster_positions(sorted_positions, threshold_degrees=8.0)
        for cluster in clusters:
            for index, position in enumerate(cluster):
                marker_point = point_on_circle(
                    center,
                    geometry.transit_marker_radius,
                    position.longitude,
                    ascendant,
                )
                label = TRANSIT_ABBREVIATIONS.get(position.body, position.body[:2])
                base_radius = geometry.transit_label_radius + (
                    index * geometry.transit_label_step
                )
                candidate_radii = (
                    base_radius,
                    base_radius - geometry.transit_label_step,
                    base_radius - (geometry.transit_label_step * 2),
                    base_radius + geometry.transit_label_step,
                    base_radius + (geometry.transit_label_step * 2),
                )
                label_rect = None
                for candidate_radius in candidate_radii:
                    label_point = point_on_circle(
                        center,
                        candidate_radius,
                        position.longitude,
                        ascendant,
                    )
                    rect = QRectF(
                        label_point.x() - ((metrics.horizontalAdvance(label) + 4) / 2),
                        label_point.y() - (metrics.height() / 2),
                        metrics.horizontalAdvance(label) + 4,
                        metrics.height(),
                    )
                    padded = rect.adjusted(-3, -2, 3, 2)
                    if not content_rect.contains(padded):
                        continue
                    if any(
                        padded.intersects(other)
                        for other in forbidden_rects + accepted_rects
                    ):
                        continue
                    label_rect = rect
                    accepted_rects.append(padded)
                    break

                if label_rect is None:
                    label_point = point_on_circle(
                        center,
                        base_radius,
                        position.longitude,
                        ascendant,
                    )
                    label_rect = QRectF(
                        label_point.x() - ((metrics.horizontalAdvance(label) + 4) / 2),
                        label_point.y() - (metrics.height() / 2),
                        metrics.horizontalAdvance(label) + 4,
                        metrics.height(),
                    )

                painter.drawEllipse(marker_point, 2.8, 2.8)
                painter.drawText(label_rect, Qt.AlignmentFlag.AlignCenter, label)

    def _draw_debug_overlay(
        self,
        painter: QPainter,
        center: QPointF,
        geometry: ChartGeometry,
        ascendant: float,
    ) -> None:
        debug_rings = (
            (geometry.outer_wheel.outer_border_radius, QColor('#ff4d4f')),
            (geometry.outer_wheel.tick_outer_radius, QColor('#ff9f43')),
            (geometry.outer_wheel.tick_inner_radius_10, QColor('#f6c343')),
            (geometry.outer_wheel.zodiac_label_band_outer_radius, QColor('#2d7dd2')),
            (geometry.outer_wheel.zodiac_label_radius, QColor('#2d7dd2')),
            (geometry.outer_wheel.zodiac_label_band_inner_radius, QColor('#4d96ff')),
            (geometry.outer_wheel.inner_border_radius, QColor('#5f8d17')),
            (geometry.planet_band_outer_radius, QColor('#8e44ad')),
            (geometry.planet_band_inner_radius, QColor('#16a085')),
            (geometry.house_outer_radius, QColor('#7f8c8d')),
            (geometry.house_inner_radius, QColor('#95a5a6')),
            (geometry.house_number_radius, QColor('#34495e')),
            (geometry.aspect_radius, QColor('#ef3f37')),
        )
        dash_pen = QPen()
        dash_pen.setStyle(Qt.PenStyle.DashLine)
        dash_pen.setWidthF(0.9)
        for radius, color in debug_rings:
            dash_pen.setColor(color)
            painter.setPen(dash_pen)
            painter.setBrush(Qt.BrushStyle.NoBrush)
            painter.drawEllipse(center, radius, radius)

        painter.setPen(QPen(QColor('#8e44ad'), 1.0))
        for position in self._chart.planet_positions:
            anchor = point_on_circle(
                center,
                geometry.planet_ring_radius,
                position.longitude,
                ascendant,
            )
            painter.setBrush(QColor('#8e44ad'))
            painter.drawEllipse(anchor, 2.4, 2.4)

        painter.setPen(QPen(QColor('#16a085'), 1.0))
        for cusp in self._chart.house_cusps:
            start = point_on_circle(
                center,
                geometry.house_inner_radius,
                cusp.longitude,
                ascendant,
            )
            end = point_on_circle(
                center,
                geometry.outer_wheel.outer_border_radius,
                cusp.longitude,
                ascendant,
            )
            painter.drawLine(start, end)

        layouts = self._compute_planet_layouts(
            center,
            geometry.planet_ring_radius,
            geometry.planet_band_outer_radius,
            geometry.planet_band_inner_radius,
            ascendant,
        )
        cluster_palette = (
            QColor('#8e44ad'),
            QColor('#16a085'),
            QColor('#e67e22'),
            QColor('#2d7dd2'),
            QColor('#d63031'),
            QColor('#00b894'),
        )
        cluster_colors: dict[tuple[float, int], QColor] = {}
        for layout in layouts:
            cluster_key = (round(layout.cluster_longitude, 3), layout.cluster_size)
            color = cluster_colors.setdefault(
                cluster_key,
                cluster_palette[len(cluster_colors) % len(cluster_palette)],
            )
            painter.setPen(QPen(color, 0.9))
            painter.drawLine(layout.connector_start, layout.connector_end)
            painter.setBrush(color)
            painter.drawEllipse(layout.base_anchor, 2.4, 2.4)
            painter.setBrush(color.lighter(120))
            painter.drawEllipse(layout.glyph_center, 3.0, 3.0)

        aspect_anchors = self._compute_aspect_anchors(center, geometry.aspect_radius, ascendant)
        painter.setPen(QPen(QColor('#ef3f37'), 0.9))
        painter.setBrush(QColor('#ef3f37'))
        for anchor in aspect_anchors.values():
            painter.drawEllipse(anchor, 2.0, 2.0)

    def _build_house_sectors(self) -> list[tuple[float, float, int]]:
        cusps = sorted(self._chart.house_cusps, key=lambda cusp: cusp.house_number)
        sectors: list[tuple[float, float, int]] = []
        for index, cusp in enumerate(cusps):
            next_cusp = cusps[(index + 1) % len(cusps)]
            sectors.append((cusp.longitude, next_cusp.longitude, cusp.house_number))
        return sectors

    def _positions_in_sector(self, sector: tuple[float, float, int]) -> list[PlanetPosition]:
        start, end, house_number = sector
        sector_positions = [
            position
            for position in self._chart.planet_positions
            if position.house == house_number
            or self._longitude_in_sector(position.longitude, start, end)
        ]
        sector_positions.sort(key=lambda item: normalize_angle(item.longitude - start))
        return sector_positions

    @staticmethod
    def _longitude_in_sector(longitude: float, start: float, end: float) -> bool:
        span = normalize_angle(end - start)
        offset = normalize_angle(longitude - start)
        return offset < span

    @staticmethod
    def _cluster_positions(
        positions: list[PlanetPosition],
        threshold_degrees: float = 7.5,
    ) -> list[list[PlanetPosition]]:
        if not positions:
            return []
        clusters: list[list[PlanetPosition]] = [[positions[0]]]
        for position in positions[1:]:
            previous = clusters[-1][-1]
            if (
                shortest_angular_distance(previous.longitude, position.longitude)
                < threshold_degrees
            ):
                clusters[-1].append(position)
            else:
                clusters.append([position])
        return clusters

    @staticmethod
    def _cluster_angle(cluster: list[PlanetPosition]) -> float:
        if len(cluster) == 1:
            return cluster[0].longitude
        base = cluster[0].longitude
        offsets = [normalize_angle(position.longitude - base) for position in cluster]
        return normalize_angle(base + sum(offsets) / len(offsets))

    @staticmethod
    def _layout_direction(point: QPointF, center: QPointF) -> str:
        dx = point.x() - center.x()
        dy = point.y() - center.y()
        if abs(dx) > abs(dy):
            return 'left' if dx < 0 else 'right'
        return 'top' if dy < 0 else 'bottom'

    @staticmethod
    def _circular_midpoint(start: float, end: float) -> float:
        span = normalize_angle(end - start)
        return normalize_angle(start + span / 2)

    @staticmethod
    def _format_cusp_degree(longitude: float) -> str:
        degree = int(longitude % 30)
        minutes = int(round(((longitude % 30) - degree) * 60))
        if minutes == 60:
            degree += 1
            minutes = 0
        return f"{degree}\N{DEGREE SIGN}\n{minutes:02d}'"

    @staticmethod
    def _sign_index(sign: str) -> int | None:
        sign_codes = {
            'Ar': 0, 'Aries': 0,
            'Ta': 1, 'Taurus': 1,
            'Ge': 2, 'Gemini': 2,
            'Cn': 3, 'Cancer': 3,
            'Le': 4, 'Leo': 4,
            'Vi': 5, 'Virgo': 5,
            'Li': 6, 'Libra': 6,
            'Sc': 7, 'Scorpio': 7,
            'Sg': 8, 'Sagittarius': 8,
            'Cp': 9, 'Capricorn': 9,
            'Aq': 10, 'Aquarius': 10,
            'Pi': 11, 'Pisces': 11,
        }
        return sign_codes.get(sign)
