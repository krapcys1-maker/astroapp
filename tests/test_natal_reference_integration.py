from __future__ import annotations

from datetime import date, time

import pytest

from app.engine.ephemeris.swiss_ephemeris_backend import SwissEphemerisBackend
from app.models.birth_data import BirthData
from app.services.natal_service import NatalService

pytestmark = pytest.mark.integration


def test_reference_natal_chart_matches_verified_olesno_case(tmp_path) -> None:
    pytest.importorskip("swisseph")
    backend = SwissEphemerisBackend(tmp_path / "ephemeris")
    service = NatalService(backend)
    birth_data = BirthData(
        person_id=1,
        birth_date=date(1985, 9, 1),
        birth_time=time(4, 45),
        city="Olesno",
        country="Poland",
        latitude=50 + 53 / 60,
        longitude=18 + 25 / 60,
        timezone_name="Europe/Warsaw",
    )

    chart = service.calculate_chart(person_id=1, birth_data=birth_data)
    positions = {position.body: position for position in chart.planet_positions}

    assert chart.calculated_at.isoformat() == "1985-09-01T02:45:00+00:00"
    assert chart.ascendant == pytest.approx(144.54, abs=0.05)
    assert chart.midheaven == pytest.approx(42.33, abs=0.05)

    expected_positions = {
        "Sun": (158.62, "Virgo"),
        "Moon": (358.49, "Pisces"),
        "Mercury": (141.06, "Leo"),
        "Venus": (124.71, "Leo"),
        "Mars": (144.32, "Leo"),
        "Jupiter": (308.76, "Aquarius"),
        "Saturn": (232.57, "Scorpio"),
        "Uranus": (254.00, "Sagittarius"),
        "Neptune": (270.88, "Capricorn"),
        "Pluto": (212.64, "Scorpio"),
    }

    for body, (longitude, sign) in expected_positions.items():
        assert positions[body].longitude == pytest.approx(longitude, abs=0.03)
        assert positions[body].sign == sign

    assert positions["Jupiter"].retrograde is True
    assert positions["Neptune"].retrograde is True
