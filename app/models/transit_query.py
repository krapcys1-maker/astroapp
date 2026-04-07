from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date


@dataclass(slots=True)
class TransitQuery:
    person_id: int
    start_date: date
    end_date: date
    orb: float
    selected_transit_bodies: tuple[str, ...] = field(default_factory=tuple)
    selected_natal_bodies: tuple[str, ...] = field(default_factory=tuple)
    selected_aspects: tuple[str, ...] = field(default_factory=tuple)
    id: int | None = None
