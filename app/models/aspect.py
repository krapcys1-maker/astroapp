from __future__ import annotations

from dataclasses import dataclass


@dataclass(slots=True)
class Aspect:
    body_a: str
    body_b: str
    aspect_type: str
    orb: float
    phase: str
    chart_id: int | None = None
