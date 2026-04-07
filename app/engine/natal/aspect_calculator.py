from __future__ import annotations

from itertools import combinations

from app.models.aspect import Aspect
from app.models.planet_position import PlanetPosition
from app.utils.angle_utils import shortest_angular_distance

MAJOR_ASPECTS = {
    "conjunction": 0.0,
    "sextile": 60.0,
    "square": 90.0,
    "trine": 120.0,
    "opposition": 180.0,
}


class AspectCalculator:
    def calculate(
        self,
        positions: list[PlanetPosition],
        orb: float,
    ) -> list[Aspect]:
        aspects: list[Aspect] = []
        for first, second in combinations(positions, 2):
            separation = shortest_angular_distance(first.longitude, second.longitude)
            for aspect_type, exact_angle in MAJOR_ASPECTS.items():
                delta = abs(separation - exact_angle)
                if delta <= orb:
                    aspects.append(
                        Aspect(
                            body_a=first.body,
                            body_b=second.body,
                            aspect_type=aspect_type,
                            orb=delta,
                            phase="n/a",
                        )
                    )
                    break
        return aspects
