from __future__ import annotations

import math

from PySide6.QtCore import QPointF, QRectF, Qt
from PySide6.QtGui import QColor, QPainter, QPaintEvent, QPen
from PySide6.QtWidgets import QWidget

from app.models.chart import Chart
from app.utils.angle_utils import normalize_angle, shortest_angular_distance

SIGN_ABBREVIATIONS = (
    "Ar",
    "Ta",
    "Ge",
    "Cn",
    "Le",
    "Vi",
    "Li",
    "Sc",
    "Sg",
    "Cp",
    "Aq",
    "Pi",
)

PLANET_ABBREVIATIONS = {
    "Sun": "Su",
    "Moon": "Mo",
    "Mercury": "Me",
    "Venus": "Ve",
    "Mars": "Ma",
    "Jupiter": "Ju",
    "Saturn": "Sa",
    "Uranus": "Ur",
    "Neptune": "Ne",
    "Pluto": "Pl",
}

ASPECT_COLORS = {
    "conjunction": QColor("#7d7d7d"),
    "sextile": QColor("#2d7dd2"),
    "square": QColor("#cf4d46"),
    "trine": QColor("#2563eb"),
    "opposition": QColor("#d62839"),
}


class NatalChartWidget(QWidget):
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._chart: Chart | None = None
        self.setObjectName("natalChartWheel")
        self.setMinimumHeight(480)

    @property
    def chart(self) -> Chart | None:
        return self._chart

    def set_chart(self, chart: Chart | None) -> None:
        self._chart = chart
        self.update()

    def paintEvent(self, event: QPaintEvent) -> None:
        del event
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.fillRect(self.rect(), QColor("#fffdfa"))
        if self._chart is None or not self._chart.house_cusps:
            self._draw_empty_state(painter)
            return

        side = min(self.width(), self.height()) - 36
        outer_radius = side / 2
        center = QPointF(self.width() / 2, self.height() / 2)
        outer_rect = QRectF(
            center.x() - outer_radius,
            center.y() - outer_radius,
            outer_radius * 2,
            outer_radius * 2,
        )
        sign_inner_radius = outer_radius - 34
        house_radius = outer_radius - 92

        painter.setPen(QPen(QColor("#203733"), 2))
        painter.drawEllipse(outer_rect)
        painter.setPen(QPen(QColor("#d4c8b9"), 1.4))
        painter.drawEllipse(center, sign_inner_radius, sign_inner_radius)
        painter.drawEllipse(center, house_radius, house_radius)

        ascendant = normalize_angle(self._chart.ascendant or self._chart.house_cusps[0].longitude)
        self._draw_sign_boundaries(painter, center, outer_radius, sign_inner_radius, ascendant)
        self._draw_house_lines(painter, center, house_radius, outer_radius, ascendant)
        placements = self._draw_planets(painter, center, sign_inner_radius - 18, ascendant)
        self._draw_aspects(painter, placements)

    def _draw_empty_state(self, painter: QPainter) -> None:
        painter.setPen(QPen(QColor("#8d877d"), 1))
        painter.drawText(
            self.rect(),
            Qt.AlignmentFlag.AlignCenter,
            "Calculate a natal chart to draw the wheel.",
        )

    def _draw_sign_boundaries(
        self,
        painter: QPainter,
        center: QPointF,
        outer_radius: float,
        inner_radius: float,
        ascendant: float,
    ) -> None:
        for sign_index, label in enumerate(SIGN_ABBREVIATIONS):
            longitude = sign_index * 30.0
            start = self._point_on_circle(center, outer_radius, longitude, ascendant)
            end = self._point_on_circle(center, inner_radius, longitude, ascendant)
            painter.setPen(QPen(QColor("#c7b8a6"), 1.2))
            painter.drawLine(start, end)

            label_point = self._point_on_circle(
                center,
                outer_radius - 16,
                longitude + 15.0,
                ascendant,
            )
            rect = QRectF(label_point.x() - 16, label_point.y() - 10, 32, 20)
            painter.setPen(QPen(QColor("#365c55"), 1))
            painter.drawText(rect, Qt.AlignmentFlag.AlignCenter, label)

    def _draw_house_lines(
        self,
        painter: QPainter,
        center: QPointF,
        inner_radius: float,
        outer_radius: float,
        ascendant: float,
    ) -> None:
        for cusp in self._chart.house_cusps:
            point = self._point_on_circle(center, outer_radius - 36, cusp.longitude, ascendant)
            inner = self._point_on_circle(center, inner_radius, cusp.longitude, ascendant)
            line_width = 2.8 if cusp.house_number in {1, 4, 7, 10} else 1.0
            color = QColor("#1f2c29") if cusp.house_number in {1, 4, 7, 10} else QColor("#9d9a94")
            painter.setPen(QPen(color, line_width))
            painter.drawLine(point, inner)

            label_point = self._point_on_circle(
                center,
                inner_radius - 20,
                cusp.longitude + 12.0,
                ascendant,
            )
            rect = QRectF(label_point.x() - 12, label_point.y() - 10, 24, 20)
            painter.setPen(QPen(QColor("#4c5a56"), 1))
            painter.drawText(rect, Qt.AlignmentFlag.AlignCenter, str(cusp.house_number))

    def _draw_planets(
        self,
        painter: QPainter,
        center: QPointF,
        radius: float,
        ascendant: float,
    ) -> dict[str, QPointF]:
        placements: dict[str, QPointF] = {}
        sorted_positions = sorted(self._chart.planet_positions, key=lambda item: item.longitude)
        placed_longitudes: list[float] = []
        stacked_count = 0

        for position in sorted_positions:
            if (
                placed_longitudes
                and shortest_angular_distance(placed_longitudes[-1], position.longitude) < 7.5
            ):
                stacked_count += 1
            else:
                stacked_count = 0
            placed_longitudes.append(position.longitude)
            adjusted_radius = radius - (stacked_count * 18)
            point = self._point_on_circle(center, adjusted_radius, position.longitude, ascendant)
            placements[position.body] = point

            painter.setPen(QPen(QColor("#163f39"), 1.2))
            painter.setBrush(QColor("#fff7ea"))
            painter.drawEllipse(point, 12, 12)

            text_rect = QRectF(point.x() - 14, point.y() - 9, 28, 18)
            label = PLANET_ABBREVIATIONS.get(position.body, position.body[:2])
            painter.drawText(text_rect, Qt.AlignmentFlag.AlignCenter, label)

        return placements

    def _draw_aspects(self, painter: QPainter, placements: dict[str, QPointF]) -> None:
        for aspect in self._chart.aspects:
            point_a = placements.get(aspect.body_a)
            point_b = placements.get(aspect.body_b)
            if point_a is None or point_b is None:
                continue
            color = ASPECT_COLORS.get(aspect.aspect_type, QColor("#888888"))
            painter.setPen(QPen(color, 1.2))
            painter.drawLine(point_a, point_b)

    @staticmethod
    def _point_on_circle(
        center: QPointF,
        radius: float,
        longitude: float,
        ascendant: float,
    ) -> QPointF:
        relative = normalize_angle(longitude - ascendant)
        screen_angle = math.radians(180.0 - relative)
        return QPointF(
            center.x() + math.cos(screen_angle) * radius,
            center.y() - math.sin(screen_angle) * radius,
        )
