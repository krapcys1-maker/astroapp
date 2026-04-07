from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path

from app.models.aspect import Aspect
from app.models.chart import Chart
from app.models.house_cusp import HouseCusp
from app.models.person import Person
from app.models.planet_position import PlanetPosition
from app.storage.db import initialize_database
from app.storage.repositories import ChartRepository, PersonRepository


def test_chart_repository_saves_and_loads_full_chart(tmp_path: Path) -> None:
    database_path = tmp_path / "charts.sqlite3"
    initialize_database(database_path)
    people = PersonRepository(database_path)
    charts = ChartRepository(database_path)

    person = people.create(Person(name="Test Client"))
    assert person.id is not None

    saved_chart = charts.save(
        Chart(
            person_id=person.id,
            chart_type="natal",
            house_system="Placidus",
            zodiac_type="tropical",
            calculated_at=datetime(2026, 4, 7, 10, 0, tzinfo=UTC),
            ascendant=15.5,
            midheaven=278.2,
            planet_positions=[
                PlanetPosition("Sun", 10.0, "Aries", 10.0, False, 1),
                PlanetPosition("Moon", 70.0, "Gemini", 10.0, False, 3),
            ],
            house_cusps=[
                HouseCusp(1, 0.0),
                HouseCusp(2, 30.0),
            ],
            aspects=[
                Aspect("Sun", "Moon", "sextile", 0.0, "n/a"),
            ],
        )
    )

    latest_chart = charts.get_latest_for_person(person.id)

    assert saved_chart.id is not None
    assert latest_chart is not None
    assert latest_chart.id == saved_chart.id
    assert len(latest_chart.planet_positions) == 2
    assert latest_chart.planet_positions[1].body == "Moon"
    assert len(latest_chart.house_cusps) == 2
    assert latest_chart.aspects[0].aspect_type == "sextile"
