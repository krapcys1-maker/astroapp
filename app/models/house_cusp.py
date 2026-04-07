from __future__ import annotations

from dataclasses import dataclass


@dataclass(slots=True)
class HouseCusp:
    house_number: int
    longitude: float
    chart_id: int | None = None
