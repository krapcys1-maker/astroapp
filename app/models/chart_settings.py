from __future__ import annotations

from dataclasses import dataclass, field

DEFAULT_NATAL_BODIES = (
    "Sun",
    "Moon",
    "Mercury",
    "Venus",
    "Mars",
    "Jupiter",
    "Saturn",
    "Uranus",
    "Neptune",
    "Pluto",
)


@dataclass(slots=True, frozen=True)
class NatalChartSettings:
    house_system: str = "Placidus"
    zodiac_type: str = "tropical"
    aspect_orb: float = 6.0
    bodies: tuple[str, ...] = field(default_factory=lambda: DEFAULT_NATAL_BODIES)
