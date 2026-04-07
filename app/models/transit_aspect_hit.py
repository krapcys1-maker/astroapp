from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime


@dataclass(slots=True)
class TransitAspectHit:
    transit_body: str
    natal_body: str
    aspect_type: str
    orb: float
    phase: str
    at_dt: datetime
