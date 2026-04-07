from __future__ import annotations

from datetime import date, time
from pathlib import Path

from app.models.birth_data import BirthData
from app.models.person import Person
from app.services.person_service import PersonService
from app.storage.db import initialize_database


def test_person_service_creates_and_updates_profile(tmp_path: Path) -> None:
    database_path = tmp_path / "profiles.sqlite3"
    initialize_database(database_path)
    service = PersonService(database_path)

    created = service.save_profile(
        Person(name="Ada Lovelace", notes="First"),
        BirthData(
            person_id=0,
            birth_date=date(1815, 12, 10),
            birth_time=time(9, 30),
            city="London",
            country="UK",
            latitude=51.5074,
            longitude=-0.1278,
            timezone_name="UTC",
        ),
    )
    assert created.person.id is not None

    service.save_profile(
        Person(id=created.person.id, name="Ada Lovelace", notes="Updated"),
        BirthData(
            person_id=created.person.id,
            birth_date=date(1815, 12, 10),
            birth_time=time(10, 0),
            city="London",
            country="UK",
            latitude=51.5074,
            longitude=-0.1278,
            timezone_name="UTC",
        ),
    )

    loaded = service.get_profile(created.person.id)

    assert loaded is not None
    assert loaded.person.notes == "Updated"
    assert loaded.birth_data is not None
    assert loaded.birth_data.birth_time == time(10, 0)
    assert len(service.list_profiles()) == 1
