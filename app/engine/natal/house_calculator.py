from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from app.engine.ephemeris import ChartAngles, EphemerisBackend, HouseCusps
from app.models.house_cusp import HouseCusp
from app.utils.angle_utils import is_angle_between


@dataclass(slots=True, frozen=True)
class CalculatedHouses:
    raw_cusps: HouseCusps
    house_cusps: list[HouseCusp]
    angles: ChartAngles


class HouseCalculator:
    def __init__(self, backend: EphemerisBackend) -> None:
        self._backend = backend

    def calculate(
        self,
        dt_utc: datetime,
        latitude: float,
        longitude: float,
        house_system: str,
    ) -> CalculatedHouses:
        cusps = self._backend.get_house_cusps(
            dt_utc,
            lat=latitude,
            lon=longitude,
            house_system=house_system,
        )
        angles = self._backend.get_angles(
            dt_utc,
            lat=latitude,
            lon=longitude,
            house_system=house_system,
        )
        return CalculatedHouses(
            raw_cusps=cusps,
            house_cusps=[
                HouseCusp(house_number=index, longitude=value)
                for index, value in enumerate(cusps.cusps, start=1)
            ],
            angles=angles,
        )

    @staticmethod
    def assign_house(longitude: float, cusps: HouseCusps) -> int:
        cusp_values = cusps.cusps
        for index, start in enumerate(cusp_values):
            end = cusp_values[(index + 1) % len(cusp_values)]
            if is_angle_between(longitude, start, end):
                return index + 1
        return 12
