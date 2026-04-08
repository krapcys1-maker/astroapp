from __future__ import annotations

import math

import pytest

from app.ui.widgets.chart_geometry import ChartGeometry, longitude_to_screen_angle


def _circular_radian_distance(a: float, b: float) -> float:
    return abs((a - b + math.pi) % (2 * math.pi) - math.pi)


def test_asc_and_dsc_are_screen_opposites() -> None:
    ascendant = 144.54
    asc_angle = longitude_to_screen_angle(ascendant, ascendant)
    dsc_angle = longitude_to_screen_angle(ascendant + 180.0, ascendant)

    assert _circular_radian_distance(asc_angle, dsc_angle) == pytest.approx(math.pi)


def test_mc_and_ic_are_screen_opposites() -> None:
    ascendant = 144.54
    midheaven = 42.33
    mc_angle = longitude_to_screen_angle(midheaven, ascendant)
    ic_angle = longitude_to_screen_angle(midheaven + 180.0, ascendant)

    assert _circular_radian_distance(mc_angle, ic_angle) == pytest.approx(math.pi)


def test_tick_band_never_enters_zodiac_label_band() -> None:
    geometry = ChartGeometry.from_outer_radius(320.0)
    outer = geometry.outer_wheel
    label_limit = outer.zodiac_label_limit

    assert outer.tick_inner_radius_1 >= label_limit
    assert outer.tick_inner_radius_5 >= label_limit
    assert outer.tick_inner_radius_10 >= label_limit
    assert outer.tick_inner_radius_10 > outer.zodiac_label_band_outer_radius
    assert outer.zodiac_label_band_outer_radius > outer.zodiac_label_radius
    assert outer.zodiac_label_radius > outer.zodiac_label_band_inner_radius
    assert outer.zodiac_label_band_inner_radius > outer.inner_border_radius


def test_planet_band_stays_between_zodiac_and_house_rings() -> None:
    geometry = ChartGeometry.from_outer_radius(320.0)

    assert geometry.planet_band_outer_radius <= geometry.outer_wheel.inner_border_radius
    assert geometry.planet_band_inner_radius < geometry.planet_band_outer_radius
    assert geometry.planet_band_inner_radius > geometry.house_outer_radius
    assert (
        geometry.planet_band_inner_radius
        <= geometry.planet_ring_radius
        <= geometry.planet_band_outer_radius
    )


def test_house_number_ring_stays_inside_house_band() -> None:
    geometry = ChartGeometry.from_outer_radius(320.0)

    assert geometry.house_inner_radius < geometry.house_number_radius < geometry.house_outer_radius
    assert geometry.house_number_marker_radius > 0
    assert (
        geometry.house_number_radius - geometry.house_number_marker_radius
        > geometry.house_inner_radius
    )
    assert (
        geometry.house_number_radius + geometry.house_number_marker_radius
        < geometry.house_outer_radius
    )


def test_cardinal_axis_radii_stay_in_expected_bands() -> None:
    geometry = ChartGeometry.from_outer_radius(320.0)

    assert geometry.cardinal_axis_outer_radius == geometry.outer_wheel.inner_border_radius
    assert geometry.cardinal_axis_inner_radius == geometry.house_outer_radius
    assert geometry.cardinal_axis_outer_radius > geometry.cardinal_axis_inner_radius
    assert geometry.cardinal_axis_label_radius > geometry.outer_wheel.outer_border_radius
    assert (
        geometry.outer_wheel.inner_border_radius
        < geometry.cardinal_degree_radius
        < geometry.outer_wheel.zodiac_label_band_inner_radius
    )
