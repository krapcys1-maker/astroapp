from __future__ import annotations

from pathlib import Path

from app.models.birth_data import BirthData
from app.models.person import Person
from app.models.person_profile import PersonProfile
from app.storage.repositories import (
    BirthDataRepository,
    PersonProfileRepository,
    PersonRepository,
)


class PersonService:
    def __init__(self, database_path: Path) -> None:
        self._people = PersonRepository(database_path)
        self._birth_data = BirthDataRepository(database_path)
        self._profiles = PersonProfileRepository(database_path)

    def list_profiles(self) -> list[PersonProfile]:
        return self._profiles.list_all()

    def get_profile(self, person_id: int) -> PersonProfile | None:
        return self._profiles.get(person_id)

    def save_profile(self, person: Person, birth_data: BirthData) -> PersonProfile:
        if person.id is None:
            saved_person = self._people.create(person)
            saved_birth_data = self._birth_data.create(
                BirthData(
                    person_id=saved_person.id or 0,
                    birth_date=birth_data.birth_date,
                    birth_time=birth_data.birth_time,
                    city=birth_data.city,
                    country=birth_data.country,
                    latitude=birth_data.latitude,
                    longitude=birth_data.longitude,
                    timezone_name=birth_data.timezone_name,
                )
            )
            return PersonProfile(person=saved_person, birth_data=saved_birth_data)

        saved_person = self._people.update(person)
        existing_birth_data = self._birth_data.get_by_person_id(person.id)
        if existing_birth_data is None:
            saved_birth_data = self._birth_data.create(birth_data)
        else:
            saved_birth_data = self._birth_data.update(birth_data)
        return PersonProfile(person=saved_person, birth_data=saved_birth_data)
