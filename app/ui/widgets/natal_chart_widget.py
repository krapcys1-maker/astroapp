from __future__ import annotations

import math
from pathlib import Path

from PySide6.QtCore import QPointF, QRectF, Qt
from PySide6.QtGui import QColor, QImage, QPainter, QPaintEvent, QPen
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

    def export_png(self, path: Path) -> bool:
        image = QImage(self.size(), QImage.Format.Format_ARGB32)
        image.fill(QColor("#fffdfa"))
        painter = QPainter(image)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        self._paint_chart(painter)
        painter.end()
        return image.save(str(path), "PNG")

    def paintEvent(self, event: QPaintEvent) -> None:
        del event
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        self._paint_chart(painter)

    def _paint_chart(self, painter: QPainter) -> None:
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
        planet_marker_radius = sign_inner_radius - 26

        painter.setPen(QPen(QColor("#203733"), 2))
        painter.drawEllipse(outer_rect)
        painter.setPen(QPen(QColor("#d4c8b9"), 1.4))
        painter.drawEllipse(center, sign_inner_radius, sign_inner_radius)
        painter.drawEllipse(center, house_radius, house_radius)

        ascendant = normalize_angle(self._chart.ascendant or self._chart.house_cusps[0].longitude)
        self._draw_sign_band(painter, center, sign_inner_radius)
        self._draw_degree_ticks(painter, center, outer_radius, ascendant)
        self._draw_sign_boundaries(painter, center, outer_radius, sign_inner_radius, ascendant)
        self._draw_house_lines(painter, center, house_radius, outer_radius, ascendant)
        self._draw_cardinal_axis_labels(
            painter,
            center,
            house_radius,
            outer_radius,
            ascendant,
        )
        placements = self._draw_planets(painter, center, planet_marker_radius, ascendant)
        self._draw_aspects(painter, placements)

    def _draw_empty_state(self, painter: QPainter) -> None:
        painter.setPen(QPen(QColor("#8d877d"), 1))
        painter.drawText(
            self.rect(),
            Qt.AlignmentFlag.AlignCenter,
            "Calculate a natal chart to draw the wheel.",
        )

    def _draw_sign_band(
        self,
        painter: QPainter,
        center: QPointF,
        inner_radius: float,
    ) -> None:
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QColor("#f7efe4"))
        painter.drawEllipse(center, inner_radius + 18, inner_radius + 18)
        painter.setBrush(Qt.BrushStyle.NoBrush)

    def _draw_degree_ticks(
        self,
        painter: QPainter,
        center: QPointF,
        outer_radius: float,
        ascendant: float,
    ) -> None:
        for degree in range(0, 360, 5):
            tick_length = 14 if degree % 30 == 0 else 8 if degree % 10 == 0 else 4
            start = self._point_on_circle(center, outer_radius, degree, ascendant)
            end = self._point_on_circle(center, outer_radius - tick_length, degree, ascendant)
            color = QColor("#998f82") if degree % 30 == 0 else QColor("#cbc0b2")
            width = 1.2 if degree % 30 == 0 else 0.8
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
        for sign_index, label in enumerate(SIGN_ABBREVIATIONS):
            longitude = sign_index * 30.0
            start = self._point_on_circle(center, outer_radius, longitude, ascendant)
            end = self._point_on_circle(center, inner_radius, longitude, ascendant)
            painter.setPen(QPen(QColor("#c7b8a6"), 1.2))
            painter.drawLine(start, end)

            label_point = self._point_on_circle(
                center,
                outer_radius - 18,
                longitude + 15.0,
                ascendant,
            )
            rect = QRectF(label_point.x() - 16, label_point.y() - 10, 32, 20)
            painter.setPen(QPen(QColor("#365c55"), 1))
            painter.drawText(rect, Qt.AlignmentFlag.AlignCenter, label)

    def _draw_cardinal_axis_labels(
        self,
        painter: QPainter,
        center: QPointF,
        inner_radius: float,
        outer_radius: float,
        ascendant: float,
    ) -> None:
        cardinal_points = {
            "ASC": normalize_angle(ascendant),
            "DSC": normalize_angle(ascendant + 180.0),
            "MC": normalize_angle(self._chart.midheaven or ascendant + 90.0),
            "IC": normalize_angle((self._chart.midheaven or ascendant + 90.0) + 180.0),
        }
        for label, longitude in cardinal_points.items():
            start = self._point_on_circle(center, outer_radius - 18, longitude, ascendant)
            end = self._point_on_circle(center, inner_radius - 8, longitude, ascendant)
            painter.setPen(QPen(QColor("#153d37"), 2.2))
            painter.drawLine(start, end)

            text_point = self._point_on_circle(center, outer_radius - 56, longitude, ascendant)
            rect = QRectF(text_point.x() - 16, text_point.y() - 10, 32, 20)
            painter.setPen(QPen(QColor("#153d37"), 1))
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
        for cluster in self._cluster_positions(sorted_positions):
            count = len(cluster)
            for index, position in enumerate(cluster):
                marker_point = self._point_on_circle(center, radius, position.longitude, ascendant)
                placements[position.body] = marker_point

                label_radius = radius - 28 - (index % 2) * 18
                tangential_shift = (index - (count - 1) / 2) * 16
                label_anchor = self._point_on_circle(
                    center,
                    label_radius,
                    position.longitude,
                    ascendant,
                )
                label_point = self._offset_tangent(
                    label_anchor,
                    position.longitude,
                    ascendant,
                    tangential_shift,
                )

                painter.setPen(QPen(QColor("#163f39"), 1.0))
                painter.setBrush(QColor("#163f39"))
                painter.drawEllipse(marker_point, 3.5, 3.5)

                painter.setPen(QPen(QColor("#98a39f"), 0.9))
                painter.drawLine(marker_point, label_point)

                painter.setPen(QPen(QColor("#163f39"), 1.0))
                painter.setBrush(QColor("#fff7ea"))
                label_rect = QRectF(label_point.x() - 20, label_point.y() - 10, 40, 20)
                painter.drawRoundedRect(label_rect, 8, 8)

                text_rect = QRectF(label_point.x() - 18, label_point.y() - 9, 36, 18)
                label = PLANET_ABBREVIATIONS.get(position.body, position.body[:2])
                painter.drawText(text_rect, Qt.AlignmentFlag.AlignCenter, label)
        return placements

    @staticmethod
    def _cluster_positions(positions) -> list[list]:
        if not positions:
            return []
        clusters: list[list] = [[positions[0]]]
        for position in positions[1:]:
            previous = clusters[-1][-1]
            if shortest_angular_distance(previous.longitude, position.longitude) < 7.5:
                clusters[-1].append(position)
            else:
                clusters.append([position])
        if len(clusters) > 1:
            first = clusters[0][0]
            last = clusters[-1][-1]
            if shortest_angular_distance(first.longitude, last.longitude) < 7.5:
                clusters[0] = clusters[-1] + clusters[0]
                clusters.pop()
        return clusters

    @staticmethod
    def _offset_tangent(
        point: QPointF,
        longitude: float,
        ascendant: float,
        shift: float,
    ) -> QPointF:
        relative = normalize_angle(longitude - ascendant)
        tangent_angle = math.radians(90.0 - relative)
        return QPointF(
            point.x() + math.cos(tangent_angle) * shift,
            point.y() - math.sin(tangent_angle) * shift,
        )

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
