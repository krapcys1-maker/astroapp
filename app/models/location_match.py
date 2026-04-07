from __future__ import annotations

from dataclasses import dataclass


@dataclass(slots=True)
class LocationMatch:
    query_text: str
    city: str
    country: str
    latitude: float
    longitude: float
    timezone_name: str
    display_name: str
    provider: str
    rank: int
    id: int | None = None
