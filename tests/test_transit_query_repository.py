from __future__ import annotations

from datetime import date
from pathlib import Path

from app.models.person import Person
from app.models.transit_query import TransitQuery
from app.storage.db import initialize_database
from app.storage.repositories import PersonRepository, TransitQueryRepository


def test_transit_query_repository_saves_and_lists_recent_queries(tmp_path: Path) -> None:
    database_path = tmp_path / "transit-queries.sqlite3"
    initialize_database(database_path)
    people = PersonRepository(database_path)
    queries = TransitQueryRepository(database_path)

    first_person = people.create(Person(name="First"))
    second_person = people.create(Person(name="Second"))
    assert first_person.id is not None
    assert second_person.id is not None

    saved_first = queries.save(
        TransitQuery(
            person_id=first_person.id,
            start_date=date(2026, 1, 1),
            end_date=date(2026, 1, 31),
            orb=3.0,
            selected_transit_bodies=("Mars",),
            selected_natal_bodies=("Sun",),
            selected_aspects=("trine",),
        )
    )
    saved_second = queries.save(
        TransitQuery(
            person_id=first_person.id,
            start_date=date(2026, 2, 1),
            end_date=date(2026, 2, 28),
            orb=4.0,
            selected_transit_bodies=("Jupiter",),
            selected_natal_bodies=("Moon",),
            selected_aspects=("sextile",),
        )
    )
    queries.save(
        TransitQuery(
            person_id=second_person.id,
            start_date=date(2026, 3, 1),
            end_date=date(2026, 3, 31),
            orb=5.0,
            selected_transit_bodies=("Saturn",),
            selected_natal_bodies=("Venus",),
            selected_aspects=("square",),
        )
    )

    recent_for_first = queries.list_recent(person_id=first_person.id)
    all_recent = queries.list_recent(limit=2)

    assert saved_first.id is not None
    assert saved_second.id is not None
    assert [query.id for query in recent_for_first] == [saved_second.id, saved_first.id]
    assert len(all_recent) == 2
    assert all_recent[0].selected_transit_bodies == ("Saturn",)
