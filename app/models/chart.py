from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime

from app.models.aspect import Aspect
from app.models.house_cusp import HouseCusp
from app.models.planet_position import PlanetPosition


@dataclass(slots=True)
class Chart:
    person_id: int
    chart_type: str
    house_system: str
    zodiac_type: str
    calculated_at: datetime
    ascendant: float | None = None
    midheaven: float | None = None
    planet_positions: list[PlanetPosition] = field(default_factory=list)
    house_cusps: list[HouseCusp] = field(default_factory=list)
    aspects: list[Aspect] = field(default_factory=list)
    id: int | None = None
