from __future__ import annotations

from datetime import UTC, datetime

import pytest

from app.engine.ephemeris.swiss_ephemeris_backend import SwissEphemerisBackend

pytestmark = pytest.mark.integration


def test_real_swiss_backend_returns_planetary_position(tmp_path) -> None:
    pytest.importorskip("swisseph")
    backend = SwissEphemerisBackend(tmp_path / "ephemeris")

    position = backend.get_planet_longitude(
        datetime(2026, 4, 7, 12, 0, tzinfo=UTC),
        "Sun",
    )

    assert position.body == "Sun"
    assert 0.0 <= position.longitude < 360.0
    assert -90.0 <= position.latitude <= 90.0
    assert position.distance_au > 0.0


def test_real_swiss_backend_returns_houses_and_angles(tmp_path) -> None:
    pytest.importorskip("swisseph")
    backend = SwissEphemerisBackend(tmp_path / "ephemeris")

    houses = backend.get_house_cusps(
        datetime(2026, 4, 7, 12, 0, tzinfo=UTC),
        lat=44.4268,
        lon=26.1025,
        house_system="Placidus",
    )
    angles = backend.get_angles(
        datetime(2026, 4, 7, 12, 0, tzinfo=UTC),
        lat=44.4268,
        lon=26.1025,
        house_system="Placidus",
    )

    assert len(houses.cusps) == 12
    assert all(0.0 <= cusp < 360.0 for cusp in houses.cusps)
    assert 0.0 <= angles.ascendant < 360.0
    assert 0.0 <= angles.midheaven < 360.0
