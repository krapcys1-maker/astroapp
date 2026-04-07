from __future__ import annotations

from datetime import datetime, time

import pytest

from app.engine.ephemeris import ChartAngles, HouseCusps, PlanetLongitude
from app.engine.natal.aspect_calculator import AspectCalculator
from app.engine.natal.chart_calculator import ChartCalculator
from app.models.birth_data import BirthData
from app.models.chart_settings import NatalChartSettings
from app.models.planet_position import PlanetPosition
from app.services.natal_service import NatalService


class FakeEphemerisBackend:
    def __init__(self) -> None:
        self.planet_calls: list[tuple[datetime, str]] = []
        self.house_calls: list[tuple[datetime, float, float, str]] = []
        self.angle_calls: list[tuple[datetime, float, float, str]] = []

    def get_planet_longitude(self, dt_utc: datetime, body: str) -> PlanetLongitude:
        self.planet_calls.append((dt_utc, body))
        positions = {
            "Sun": PlanetLongitude("Sun", 10.0, 0.0, 1.0, 1.0, 0),
            "Moon": PlanetLongitude("Moon", 70.0, 1.0, 1.1, 12.0, 0),
            "Mercury": PlanetLongitude("Mercury", 130.0, 0.5, 0.8, 1.4, 0),
            "Venus": PlanetLongitude("Venus", 190.0, -0.2, 0.7, 1.2, 0),
            "Mars": PlanetLongitude("Mars", 100.0, -0.5, 1.5, 0.7, 0),
            "Jupiter": PlanetLongitude("Jupiter", 250.0, 0.1, 5.2, 0.2, 0),
            "Saturn": PlanetLongitude("Saturn", 310.0, -0.1, 9.5, 0.1, 0),
            "Uranus": PlanetLongitude("Uranus", 40.0, 0.3, 19.0, 0.05, 0),
            "Neptune": PlanetLongitude("Neptune", 160.0, -0.4, 30.0, 0.03, 0),
            "Pluto": PlanetLongitude("Pluto", 220.0, 0.2, 39.0, -0.01, 0),
        }
        return positions[body]

    def get_house_cusps(
        self,
        dt_utc: datetime,
        lat: float,
        lon: float,
        house_system: str,
    ) -> HouseCusps:
        self.house_calls.append((dt_utc, lat, lon, house_system))
        return HouseCusps(
            house_system=house_system,
            cusps=(0.0, 30.0, 60.0, 90.0, 120.0, 150.0, 180.0, 210.0, 240.0, 270.0, 300.0, 330.0),
        )

    def get_angles(
        self,
        dt_utc: datetime,
        lat: float,
        lon: float,
        house_system: str,
    ) -> ChartAngles:
        self.angle_calls.append((dt_utc, lat, lon, house_system))
        return ChartAngles(ascendant=15.0, midheaven=280.0)


def test_aspect_calculator_detects_major_aspects() -> None:
    positions = [
        PlanetPosition("Sun", 10.0, "Aries", 10.0, False, 1),
        PlanetPosition("Moon", 70.0, "Gemini", 10.0, False, 3),
        PlanetPosition("Mars", 100.0, "Cancer", 10.0, False, 4),
    ]

    aspects = AspectCalculator().calculate(positions, orb=2.0)

    aspect_pairs = {(aspect.body_a, aspect.body_b, aspect.aspect_type) for aspect in aspects}
    assert ("Sun", "Moon", "sextile") in aspect_pairs
    assert ("Sun", "Mars", "square") in aspect_pairs
    assert len(aspects) == 2


def test_chart_calculator_assembles_chart_from_backend_data() -> None:
    backend = FakeEphemerisBackend()
    calculator = ChartCalculator(backend)
    birth_data = BirthData(
        person_id=1,
        birth_date=datetime(1990, 1, 1).date(),
        birth_time=time(6, 30),
        city="New York",
        country="USA",
        latitude=40.7128,
        longitude=-74.0060,
        timezone_name="America/New_York",
    )
    settings = NatalChartSettings(
        bodies=("Sun", "Moon", "Mars"),
        aspect_orb=2.0,
    )

    chart = calculator.calculate(
        birth_data=birth_data,
        settings=settings,
        person_id=1,
    )

    assert chart.chart_type == "natal"
    assert chart.ascendant == pytest.approx(15.0)
    assert chart.midheaven == pytest.approx(280.0)
    assert [position.body for position in chart.planet_positions] == ["Sun", "Moon", "Mars"]
    assert chart.planet_positions[0].sign == "Aries"
    assert chart.planet_positions[1].house == 3
    assert len(chart.house_cusps) == 12
    assert {aspect.aspect_type for aspect in chart.aspects} == {"sextile", "square"}
    assert chart.calculated_at.isoformat() == "1990-01-01T11:30:00+00:00"


def test_natal_service_uses_default_settings() -> None:
    backend = FakeEphemerisBackend()
    service = NatalService(backend)
    birth_data = BirthData(
        person_id=5,
        birth_date=datetime(1990, 1, 1).date(),
        birth_time=time(6, 30),
        city="New York",
        country="USA",
        latitude=40.7128,
        longitude=-74.0060,
        timezone_name="America/New_York",
    )

    chart = service.calculate_chart(person_id=5, birth_data=birth_data)

    assert chart.person_id == 5
    assert chart.house_system == "Placidus"
    assert backend.planet_calls
