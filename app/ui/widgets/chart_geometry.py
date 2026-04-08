from __future__ import annotations

import math
from dataclasses import dataclass

from PySide6.QtCore import QPointF

from app.utils.angle_utils import normalize_angle


@dataclass(frozen=True)
class OuterWheelGeometry:
    outer_border_radius: float
    tick_outer_radius: float
    tick_inner_radius_1: float
    tick_inner_radius_5: float
    tick_inner_radius_10: float
    zodiac_label_band_outer_radius: float
    zodiac_label_band_inner_radius: float
    zodiac_label_radius: float
    zodiac_label_clearance: float
    zodiac_glyph_outer_radius: float
    inner_border_radius: float

    @property
    def zodiac_label_limit(self) -> float:
        return self.zodiac_label_radius + self.zodiac_label_clearance


@dataclass(frozen=True)
class ChartGeometry:
    outer_wheel: OuterWheelGeometry
    house_outer_radius: float
    house_inner_radius: float
    house_number_radius: float
    house_number_marker_radius: float
    cardinal_axis_outer_radius: float
    cardinal_axis_inner_radius: float
    cardinal_axis_label_radius: float
    cardinal_degree_radius: float
    aspect_radius: float
    planet_line_radius: float
    planet_ring_radius: float
    planet_band_outer_radius: float
    planet_band_inner_radius: float
    transit_marker_radius: float
    transit_label_radius: float
    transit_label_step: float
    center_clear_radius: float

    @classmethod
    def from_outer_radius(cls, outer_radius: float) -> ChartGeometry:
        outer_wheel = OuterWheelGeometry(
            outer_border_radius=outer_radius,
            tick_outer_radius=outer_radius - 2,
            tick_inner_radius_1=outer_radius - 9,
            tick_inner_radius_5=outer_radius - 13,
            tick_inner_radius_10=outer_radius - 17,
            zodiac_label_band_outer_radius=outer_radius - 23,
            zodiac_label_band_inner_radius=outer_radius - 35,
            zodiac_label_radius=outer_radius - 29,
            zodiac_label_clearance=5,
            zodiac_glyph_outer_radius=outer_radius + 18,
            inner_border_radius=outer_radius - 38,
        )
        house_outer_radius = outer_radius - 106
        house_inner_radius = outer_radius - 150
        aspect_radius = house_inner_radius - 6
        planet_band_outer_radius = outer_wheel.inner_border_radius - 8
        planet_line_radius = planet_band_outer_radius
        planet_ring_radius = planet_band_outer_radius - 8
        planet_band_inner_radius = house_outer_radius + 16
        transit_marker_radius = outer_wheel.outer_border_radius + 4
        transit_label_radius = outer_wheel.zodiac_glyph_outer_radius + 12
        transit_label_step = 14.0
        return cls(
            outer_wheel=outer_wheel,
            house_outer_radius=house_outer_radius,
            house_inner_radius=house_inner_radius,
            house_number_radius=house_inner_radius
            + ((house_outer_radius - house_inner_radius) * 0.56),
            house_number_marker_radius=11.0,
            cardinal_axis_outer_radius=outer_wheel.inner_border_radius,
            cardinal_axis_inner_radius=house_outer_radius,
            cardinal_axis_label_radius=outer_wheel.outer_border_radius + 14,
            cardinal_degree_radius=outer_wheel.zodiac_label_band_inner_radius - 2,
            aspect_radius=aspect_radius,
            planet_line_radius=planet_line_radius,
            planet_ring_radius=planet_ring_radius,
            planet_band_outer_radius=planet_band_outer_radius,
            planet_band_inner_radius=planet_band_inner_radius,
            transit_marker_radius=transit_marker_radius,
            transit_label_radius=transit_label_radius,
            transit_label_step=transit_label_step,
            center_clear_radius=house_inner_radius,
        )


def longitude_to_screen_angle(longitude: float, ascendant: float) -> float:
    relative = normalize_angle(ascendant - longitude)
    return math.radians(180.0 - relative)


def point_on_circle(
    center: QPointF,
    radius: float,
    longitude: float,
    ascendant: float,
) -> QPointF:
    screen_angle = longitude_to_screen_angle(longitude, ascendant)
    return QPointF(
        center.x() + math.cos(screen_angle) * radius,
        center.y() - math.sin(screen_angle) * radius,
    )


def tangent_unit(longitude: float, ascendant: float) -> tuple[float, float]:
    screen_angle = longitude_to_screen_angle(longitude, ascendant)
    return math.sin(screen_angle), math.cos(screen_angle)
