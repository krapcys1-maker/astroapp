from __future__ import annotations

from dataclasses import dataclass
from datetime import date, time


@dataclass(slots=True)
class BirthData:
    person_id: int
    birth_date: date
    birth_time: time
    city: str
    country: str
    latitude: float
    longitude: float
    timezone_name: str
