from __future__ import annotations

import sqlite3
from datetime import date, time
from pathlib import Path

import pytest

from app.models.birth_data import BirthData
from app.models.person import Person
from app.storage.db import initialize_database
from app.storage.repositories import BirthDataRepository, PersonRepository


def test_person_repository_create_read_update_and_list(tmp_path: Path) -> None:
    database_path = tmp_path / "people.sqlite3"
    initialize_database(database_path)

    repository = PersonRepository(database_path)

    created = repository.create(Person(name="Ada Lovelace", notes="First client"))
    assert created.id is not None

    updated = repository.update(
        Person(id=created.id, name="Ada Lovelace", notes="Updated notes")
    )
    loaded = repository.get(created.id)
    people = repository.list_all()

    assert updated.notes == "Updated notes"
    assert loaded == updated
    assert people == [updated]


def test_birth_data_repository_create_read_update_round_trip(tmp_path: Path) -> None:
    database_path = tmp_path / "birth-data.sqlite3"
    initialize_database(database_path)

    people = PersonRepository(database_path)
    birth_data_repository = BirthDataRepository(database_path)

    person = people.create(Person(name="Grace Hopper"))
    assert person.id is not None

    created = birth_data_repository.create(
        BirthData(
            person_id=person.id,
            birth_date=date(1906, 12, 9),
            birth_time=time(1, 20),
            city="New York",
            country="USA",
            latitude=40.7128,
            longitude=-74.0060,
            timezone_name="America/New_York",
        )
    )

    updated = birth_data_repository.update(
        BirthData(
            person_id=created.person_id,
            birth_date=date(1906, 12, 9),
            birth_time=time(2, 15),
            city="Arlington",
            country="USA",
            latitude=38.8816,
            longitude=-77.0910,
            timezone_name="America/New_York",
        )
    )
    loaded = birth_data_repository.get_by_person_id(created.person_id)

    assert loaded == updated
    assert loaded.birth_time == time(2, 15)
    assert loaded.city == "Arlington"


def test_person_repository_update_requires_existing_row(tmp_path: Path) -> None:
    database_path = tmp_path / "missing-person.sqlite3"
    initialize_database(database_path)

    repository = PersonRepository(database_path)

    with pytest.raises(LookupError):
        repository.update(Person(id=123, name="Missing"))


def test_birth_data_repository_update_requires_existing_row(tmp_path: Path) -> None:
    database_path = tmp_path / "missing-birth-data.sqlite3"
    initialize_database(database_path)

    repository = BirthDataRepository(database_path)

    with pytest.raises(LookupError):
        repository.update(
            BirthData(
                person_id=123,
                birth_date=date(2000, 1, 1),
                birth_time=time(12, 0),
                city="Test",
                country="Test",
                latitude=1.0,
                longitude=2.0,
                timezone_name="UTC",
            )
        )


def test_birth_data_repository_requires_existing_person(tmp_path: Path) -> None:
    database_path = tmp_path / "fk.sqlite3"
    initialize_database(database_path)

    repository = BirthDataRepository(database_path)

    with pytest.raises(sqlite3.IntegrityError):
        repository.create(
            BirthData(
                person_id=999,
                birth_date=date(2000, 1, 1),
                birth_time=time(12, 0),
                city="Test",
                country="Test",
                latitude=1.0,
                longitude=2.0,
                timezone_name="UTC",
            )
        )
