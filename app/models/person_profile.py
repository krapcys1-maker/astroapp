from __future__ import annotations

from dataclasses import dataclass

from app.models.birth_data import BirthData
from app.models.person import Person


@dataclass(slots=True)
class PersonProfile:
    person: Person
    birth_data: BirthData | None = None
