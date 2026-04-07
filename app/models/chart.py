from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime


@dataclass(slots=True)
class Chart:
    person_id: int
    chart_type: str
    house_system: str
    zodiac_type: str
    calculated_at: datetime
    id: int | None = None
