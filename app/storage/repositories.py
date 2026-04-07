from __future__ import annotations

from datetime import date, time
from pathlib import Path
from sqlite3 import Row

from app.models.birth_data import BirthData
from app.models.person import Person
from app.storage.db import connect_sqlite


def _parse_date(value: str) -> date:
    return date.fromisoformat(value)


def _parse_time(value: str) -> time:
    return time.fromisoformat(value)


def _person_from_row(row: Row) -> Person:
    return Person(
        id=row["id"],
        name=row["name"],
        notes=row["notes"],
    )


def _birth_data_from_row(row: Row) -> BirthData:
    return BirthData(
        person_id=row["person_id"],
        birth_date=_parse_date(row["birth_date"]),
        birth_time=_parse_time(row["birth_time"]),
        city=row["city"],
        country=row["country"],
        latitude=row["latitude"],
        longitude=row["longitude"],
        timezone_name=row["timezone_name"],
    )


class PersonRepository:
    def __init__(self, database_path: Path) -> None:
        self._database_path = database_path

    def create(self, person: Person) -> Person:
        with connect_sqlite(self._database_path) as connection:
            cursor = connection.execute(
                """
                INSERT INTO people(name, notes)
                VALUES (?, ?)
                """,
                (person.name, person.notes),
            )
        return Person(id=cursor.lastrowid, name=person.name, notes=person.notes)

    def get(self, person_id: int) -> Person | None:
        with connect_sqlite(self._database_path) as connection:
            row = connection.execute(
                """
                SELECT id, name, notes
                FROM people
                WHERE id = ?
                """,
                (person_id,),
            ).fetchone()
        return None if row is None else _person_from_row(row)

    def list_all(self) -> list[Person]:
        with connect_sqlite(self._database_path) as connection:
            rows = connection.execute(
                """
                SELECT id, name, notes
                FROM people
                ORDER BY name COLLATE NOCASE, id
                """
            ).fetchall()
        return [_person_from_row(row) for row in rows]

    def update(self, person: Person) -> Person:
        if person.id is None:
            msg = "Person id is required for update."
            raise ValueError(msg)
        with connect_sqlite(self._database_path) as connection:
            cursor = connection.execute(
                """
                UPDATE people
                SET name = ?, notes = ?
                WHERE id = ?
                """,
                (person.name, person.notes, person.id),
            )
        if cursor.rowcount == 0:
            msg = f"Person with id={person.id} does not exist."
            raise LookupError(msg)
        return person


class BirthDataRepository:
    def __init__(self, database_path: Path) -> None:
        self._database_path = database_path

    def create(self, birth_data: BirthData) -> BirthData:
        with connect_sqlite(self._database_path) as connection:
            connection.execute(
                """
                INSERT INTO birth_data(
                    person_id,
                    birth_date,
                    birth_time,
                    city,
                    country,
                    latitude,
                    longitude,
                    timezone_name
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    birth_data.person_id,
                    birth_data.birth_date.isoformat(),
                    birth_data.birth_time.isoformat(),
                    birth_data.city,
                    birth_data.country,
                    birth_data.latitude,
                    birth_data.longitude,
                    birth_data.timezone_name,
                ),
            )
        return birth_data

    def get_by_person_id(self, person_id: int) -> BirthData | None:
        with connect_sqlite(self._database_path) as connection:
            row = connection.execute(
                """
                SELECT
                    person_id,
                    birth_date,
                    birth_time,
                    city,
                    country,
                    latitude,
                    longitude,
                    timezone_name
                FROM birth_data
                WHERE person_id = ?
                """,
                (person_id,),
            ).fetchone()
        return None if row is None else _birth_data_from_row(row)

    def update(self, birth_data: BirthData) -> BirthData:
        with connect_sqlite(self._database_path) as connection:
            cursor = connection.execute(
                """
                UPDATE birth_data
                SET
                    birth_date = ?,
                    birth_time = ?,
                    city = ?,
                    country = ?,
                    latitude = ?,
                    longitude = ?,
                    timezone_name = ?
                WHERE person_id = ?
                """,
                (
                    birth_data.birth_date.isoformat(),
                    birth_data.birth_time.isoformat(),
                    birth_data.city,
                    birth_data.country,
                    birth_data.latitude,
                    birth_data.longitude,
                    birth_data.timezone_name,
                    birth_data.person_id,
                ),
            )
        if cursor.rowcount == 0:
            msg = f"Birth data for person_id={birth_data.person_id} does not exist."
            raise LookupError(msg)
        return birth_data
