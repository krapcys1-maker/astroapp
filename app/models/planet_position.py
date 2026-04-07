from __future__ import annotations

from dataclasses import dataclass


@dataclass(slots=True)
class PlanetPosition:
    body: str
    longitude: float
    sign: str
    degree_in_sign: float
    retrograde: bool
    house: int | None = None
    chart_id: int | None = None
