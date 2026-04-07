from __future__ import annotations

from datetime import UTC, date, datetime
from pathlib import Path

import pytest

from app.engine.ephemeris import ChartAngles, HouseCusps, PlanetLongitude
from app.models.chart import Chart
from app.models.person import Person
from app.models.planet_position import PlanetPosition
from app.models.transit_query import TransitQuery
from app.services.transit_service import TransitService
from app.storage.db import initialize_database
from app.storage.repositories import ChartRepository, PersonRepository


class LinearTransitBackend:
    def __init__(self, motions: dict[str, tuple[float, float]]) -> None:
        self._motions = motions
        self._epoch = datetime(2026, 1, 1, tzinfo=UTC)

    def get_planet_longitude(self, dt_utc: datetime, body: str) -> PlanetLongitude:
        base, speed_per_day = self._motions[body]
        delta_days = (dt_utc - self._epoch).total_seconds() / 86_400
        longitude = base + speed_per_day * delta_days
        return PlanetLongitude(
            body=body,
            longitude=longitude,
            latitude=0.0,
            distance_au=1.0,
            speed_longitude=speed_per_day,
            retflag=0,
        )

    def get_house_cusps(
        self,
        dt_utc: datetime,
        lat: float,
        lon: float,
        house_system: str,
    ) -> HouseCusps:
        del dt_utc, lat, lon, house_system
        return HouseCusps(
            "P",
            (0.0, 30.0, 60.0, 90.0, 120.0, 150.0, 180.0, 210.0, 240.0, 270.0, 300.0, 330.0),
        )

    def get_angles(
        self,
        dt_utc: datetime,
        lat: float,
        lon: float,
        house_system: str,
    ) -> ChartAngles:
        del dt_utc, lat, lon, house_system
        return ChartAngles(ascendant=0.0, midheaven=90.0)


def build_natal_chart(person_id: int, natal_longitude: float) -> Chart:
    return Chart(
        person_id=person_id,
        chart_type="natal",
        house_system="Placidus",
        zodiac_type="tropical",
        calculated_at=datetime(2026, 1, 1, tzinfo=UTC),
        planet_positions=[
            PlanetPosition("Sun", natal_longitude, "Aries", natal_longitude % 30, False, 1)
        ],
    )


def test_transit_service_returns_empty_when_never_entering_orb() -> None:
    backend = LinearTransitBackend({"Mars": (0.0, 2.0)})
    service = TransitService(backend)
    chart = build_natal_chart(person_id=1, natal_longitude=100.0)
    query = TransitQuery(
        person_id=1,
        start_date=date(2026, 1, 1),
        end_date=date(2026, 1, 2),
        orb=2.0,
        selected_transit_bodies=("Mars",),
        selected_natal_bodies=("Sun",),
        selected_aspects=("conjunction",),
    )

    events = service.search(query, natal_chart=chart)

    assert events == []


def test_transit_service_detects_enter_exit_and_exact_inside_range() -> None:
    backend = LinearTransitBackend({"Mars": (13.0, 3.0)})
    service = TransitService(backend)
    chart = build_natal_chart(person_id=1, natal_longitude=20.0)
    query = TransitQuery(
        person_id=1,
        start_date=date(2026, 1, 2),
        end_date=date(2026, 1, 4),
        orb=3.0,
        selected_transit_bodies=("Mars",),
        selected_natal_bodies=("Sun",),
        selected_aspects=("conjunction",),
    )

    events = service.search(query, natal_chart=chart)

    assert len(events) == 1
    event = events[0]
    assert abs((event.start_dt - datetime(2026, 1, 2, 8, 0, tzinfo=UTC)).total_seconds()) <= 60
    assert event.exact_dt is not None
    assert abs((event.exact_dt - datetime(2026, 1, 3, 8, 0, tzinfo=UTC)).total_seconds()) <= 60
    assert event.end_dt is not None
    assert abs((event.end_dt - datetime(2026, 1, 4, 8, 0, tzinfo=UTC)).total_seconds()) <= 60
    assert event.exact_orb == pytest.approx(0.0)


def test_transit_service_marks_event_when_search_starts_already_in_orb() -> None:
    backend = LinearTransitBackend({"Mars": (18.0, 1.0)})
    service = TransitService(backend)
    chart = build_natal_chart(person_id=1, natal_longitude=20.0)
    query = TransitQuery(
        person_id=1,
        start_date=date(2026, 1, 1),
        end_date=date(2026, 1, 1),
        orb=3.0,
        selected_transit_bodies=("Mars",),
        selected_natal_bodies=("Sun",),
        selected_aspects=("conjunction",),
    )

    events = service.search(query, natal_chart=chart)

    assert len(events) == 1
    event = events[0]
    assert event.start_dt == datetime(2026, 1, 1, 0, 0, tzinfo=UTC)
    assert event.end_dt is None
    assert event.exact_dt is None
    assert event.phase == "applying"


def test_transit_service_marks_event_when_it_ends_after_search_window() -> None:
    backend = LinearTransitBackend({"Mars": (21.0, 1.0)})
    service = TransitService(backend)
    chart = build_natal_chart(person_id=1, natal_longitude=20.0)
    query = TransitQuery(
        person_id=1,
        start_date=date(2026, 1, 1),
        end_date=date(2026, 1, 1),
        orb=3.0,
        selected_transit_bodies=("Mars",),
        selected_natal_bodies=("Sun",),
        selected_aspects=("conjunction",),
    )

    events = service.search(query, natal_chart=chart)

    assert len(events) == 1
    event = events[0]
    assert event.start_dt == datetime(2026, 1, 1, 0, 0, tzinfo=UTC)
    assert event.end_dt is None
    assert event.exact_dt is None
    assert event.phase == "separating"


def test_transit_service_can_load_latest_natal_chart_from_repository(tmp_path: Path) -> None:
    database_path = tmp_path / "transits.sqlite3"
    initialize_database(database_path)
    people = PersonRepository(database_path)
    charts = ChartRepository(database_path)
    person = people.create(Person(name="Transit Client"))
    assert person.id is not None
    charts.save(build_natal_chart(person.id, natal_longitude=20.0))

    backend = LinearTransitBackend({"Mars": (13.0, 3.0)})
    service = TransitService(backend, database_path=database_path)
    query = TransitQuery(
        person_id=person.id,
        start_date=date(2026, 1, 2),
        end_date=date(2026, 1, 4),
        orb=3.0,
        selected_transit_bodies=("Mars",),
        selected_natal_bodies=("Sun",),
        selected_aspects=("conjunction",),
    )

    events = service.search(query)

    assert len(events) == 1
    assert events[0].natal_body == "Sun"
