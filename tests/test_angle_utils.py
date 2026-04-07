from __future__ import annotations

import pytest

from app.utils.angle_utils import (
    degree_in_sign,
    is_angle_between,
    normalize_angle,
    shortest_angular_distance,
    zodiac_sign,
)


def test_normalize_angle_wraps_values() -> None:
    assert normalize_angle(361.5) == pytest.approx(1.5)
    assert normalize_angle(-45.0) == pytest.approx(315.0)


def test_shortest_angular_distance_uses_smallest_arc() -> None:
    assert shortest_angular_distance(350.0, 10.0) == pytest.approx(20.0)


def test_angle_helpers_report_sign_degree_and_ranges() -> None:
    longitude = 133.25

    assert zodiac_sign(longitude) == "Leo"
    assert degree_in_sign(longitude) == pytest.approx(13.25)
    assert is_angle_between(355.0, 330.0, 30.0) is True
