from __future__ import annotations

from datetime import date, datetime, time
from pathlib import Path
from sqlite3 import Row

from app.models.aspect import Aspect
from app.models.birth_data import BirthData
from app.models.chart import Chart
from app.models.house_cusp import HouseCusp
from app.models.person import Person
from app.models.person_profile import PersonProfile
from app.models.planet_position import PlanetPosition
from app.storage.db import connect_sqlite


def _parse_date(value: str) -> date:
    return date.fromisoformat(value)


def _parse_time(value: str) -> time:
    return time.fromisoformat(value)


def _parse_datetime(value: str) -> datetime:
    return datetime.fromisoformat(value)


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


def _chart_from_row(row: Row) -> Chart:
    return Chart(
        id=row["id"],
        person_id=row["person_id"],
        chart_type=row["chart_type"],
        house_system=row["house_system"],
        zodiac_type=row["zodiac_type"],
        calculated_at=_parse_datetime(row["calculated_at"]),
        ascendant=row["ascendant"],
        midheaven=row["midheaven"],
    )


def _planet_position_from_row(row: Row) -> PlanetPosition:
    return PlanetPosition(
        chart_id=row["chart_id"],
        body=row["body"],
        longitude=row["longitude"],
        sign=row["sign"],
        degree_in_sign=row["degree_in_sign"],
        retrograde=bool(row["retrograde"]),
        house=row["house"],
    )


def _house_cusp_from_row(row: Row) -> HouseCusp:
    return HouseCusp(
        chart_id=row["chart_id"],
        house_number=row["house_number"],
        longitude=row["longitude"],
    )


def _aspect_from_row(row: Row) -> Aspect:
    return Aspect(
        chart_id=row["chart_id"],
        body_a=row["body_a"],
        body_b=row["body_b"],
        aspect_type=row["aspect_type"],
        orb=row["orb"],
        phase=row["phase"],
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


class PersonProfileRepository:
    def __init__(self, database_path: Path) -> None:
        self._people = PersonRepository(database_path)
        self._birth_data = BirthDataRepository(database_path)

    def list_all(self) -> list[PersonProfile]:
        return [
            PersonProfile(
                person=person,
                birth_data=self._birth_data.get_by_person_id(person.id),
            )
            for person in self._people.list_all()
            if person.id is not None
        ]

    def get(self, person_id: int) -> PersonProfile | None:
        person = self._people.get(person_id)
        if person is None:
            return None
        return PersonProfile(
            person=person,
            birth_data=self._birth_data.get_by_person_id(person_id),
        )


class ChartRepository:
    def __init__(self, database_path: Path) -> None:
        self._database_path = database_path

    def save(self, chart: Chart) -> Chart:
        with connect_sqlite(self._database_path) as connection:
            cursor = connection.execute(
                """
                INSERT INTO charts(
                    person_id,
                    chart_type,
                    house_system,
                    zodiac_type,
                    calculated_at,
                    ascendant,
                    midheaven
                )
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    chart.person_id,
                    chart.chart_type,
                    chart.house_system,
                    chart.zodiac_type,
                    chart.calculated_at.isoformat(),
                    chart.ascendant,
                    chart.midheaven,
                ),
            )
            chart_id = cursor.lastrowid
            for position in chart.planet_positions:
                connection.execute(
                    """
                    INSERT INTO planet_positions(
                        chart_id,
                        body,
                        longitude,
                        sign,
                        degree_in_sign,
                        retrograde,
                        house
                    )
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        chart_id,
                        position.body,
                        position.longitude,
                        position.sign,
                        position.degree_in_sign,
                        int(position.retrograde),
                        position.house,
                    ),
                )
            for house_cusp in chart.house_cusps:
                connection.execute(
                    """
                    INSERT INTO house_cusps(chart_id, house_number, longitude)
                    VALUES (?, ?, ?)
                    """,
                    (
                        chart_id,
                        house_cusp.house_number,
                        house_cusp.longitude,
                    ),
                )
            for aspect in chart.aspects:
                connection.execute(
                    """
                    INSERT INTO aspects(chart_id, body_a, body_b, aspect_type, orb, phase)
                    VALUES (?, ?, ?, ?, ?, ?)
                    """,
                    (
                        chart_id,
                        aspect.body_a,
                        aspect.body_b,
                        aspect.aspect_type,
                        aspect.orb,
                        aspect.phase,
                    ),
                )
        return self.get(chart_id) or chart

    def get(self, chart_id: int) -> Chart | None:
        with connect_sqlite(self._database_path) as connection:
            row = connection.execute(
                """
                SELECT
                    id,
                    person_id,
                    chart_type,
                    house_system,
                    zodiac_type,
                    calculated_at,
                    ascendant,
                    midheaven
                FROM charts
                WHERE id = ?
                """,
                (chart_id,),
            ).fetchone()
            if row is None:
                return None
            chart = _chart_from_row(row)
            chart.planet_positions = self._get_positions(connection, chart_id)
            chart.house_cusps = self._get_house_cusps(connection, chart_id)
            chart.aspects = self._get_aspects(connection, chart_id)
            return chart

    def get_latest_for_person(
        self,
        person_id: int,
        *,
        chart_type: str = "natal",
    ) -> Chart | None:
        with connect_sqlite(self._database_path) as connection:
            row = connection.execute(
                """
                SELECT
                    id,
                    person_id,
                    chart_type,
                    house_system,
                    zodiac_type,
                    calculated_at,
                    ascendant,
                    midheaven
                FROM charts
                WHERE person_id = ? AND chart_type = ?
                ORDER BY calculated_at DESC, id DESC
                LIMIT 1
                """,
                (person_id, chart_type),
            ).fetchone()
            if row is None:
                return None
            chart = _chart_from_row(row)
            chart.planet_positions = self._get_positions(connection, chart.id or 0)
            chart.house_cusps = self._get_house_cusps(connection, chart.id or 0)
            chart.aspects = self._get_aspects(connection, chart.id or 0)
            return chart

    @staticmethod
    def _get_positions(connection, chart_id: int) -> list[PlanetPosition]:
        rows = connection.execute(
            """
            SELECT chart_id, body, longitude, sign, degree_in_sign, retrograde, house
            FROM planet_positions
            WHERE chart_id = ?
            ORDER BY id
            """,
            (chart_id,),
        ).fetchall()
        return [_planet_position_from_row(row) for row in rows]

    @staticmethod
    def _get_house_cusps(connection, chart_id: int) -> list[HouseCusp]:
        rows = connection.execute(
            """
            SELECT chart_id, house_number, longitude
            FROM house_cusps
            WHERE chart_id = ?
            ORDER BY house_number
            """,
            (chart_id,),
        ).fetchall()
        return [_house_cusp_from_row(row) for row in rows]

    @staticmethod
    def _get_aspects(connection, chart_id: int) -> list[Aspect]:
        rows = connection.execute(
            """
            SELECT chart_id, body_a, body_b, aspect_type, orb, phase
            FROM aspects
            WHERE chart_id = ?
            ORDER BY id
            """,
            (chart_id,),
        ).fetchall()
        return [_aspect_from_row(row) for row in rows]
