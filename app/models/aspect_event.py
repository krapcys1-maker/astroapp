from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime


@dataclass(slots=True)
class AspectEvent:
    transit_body: str
    natal_body: str
    aspect_type: str
    start_dt: datetime
    exact_dt: datetime | None
    end_dt: datetime | None
    exact_orb: float | None
    phase: str
    query_id: int | None = None
    id: int | None = None
