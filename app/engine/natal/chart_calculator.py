from __future__ import annotations

from datetime import datetime

from app.engine.ephemeris import EphemerisBackend
from app.engine.natal.aspect_calculator import AspectCalculator
from app.engine.natal.house_calculator import HouseCalculator
from app.models.birth_data import BirthData
from app.models.chart import Chart
from app.models.chart_settings import NatalChartSettings
from app.models.planet_position import PlanetPosition
from app.utils.angle_utils import degree_in_sign, zodiac_sign
from app.utils.time_utils import birth_data_to_utc_datetime


class ChartCalculator:
    def __init__(
        self,
        backend: EphemerisBackend,
        house_calculator: HouseCalculator | None = None,
        aspect_calculator: AspectCalculator | None = None,
    ) -> None:
        self._backend = backend
        self._house_calculator = house_calculator or HouseCalculator(backend)
        self._aspect_calculator = aspect_calculator or AspectCalculator()

    def calculate(
        self,
        birth_data: BirthData,
        settings: NatalChartSettings,
        *,
        person_id: int,
        calculated_at: datetime | None = None,
    ) -> Chart:
        dt_utc = birth_data_to_utc_datetime(birth_data)
        houses = self._house_calculator.calculate(
            dt_utc,
            latitude=birth_data.latitude,
            longitude=birth_data.longitude,
            house_system=settings.house_system,
        )

        positions: list[PlanetPosition] = []
        for body in settings.bodies:
            position = self._backend.get_planet_longitude(dt_utc, body)
            positions.append(
                PlanetPosition(
                    body=body,
                    longitude=position.longitude,
                    sign=zodiac_sign(position.longitude),
                    degree_in_sign=degree_in_sign(position.longitude),
                    retrograde=position.retrograde,
                    house=self._house_calculator.assign_house(
                        position.longitude,
                        houses.raw_cusps,
                    ),
                )
            )

        aspects = self._aspect_calculator.calculate(
            positions,
            orb=settings.aspect_orb,
        )
        return Chart(
            person_id=person_id,
            chart_type="natal",
            house_system=settings.house_system,
            zodiac_type=settings.zodiac_type,
            calculated_at=calculated_at or dt_utc,
            ascendant=houses.angles.ascendant,
            midheaven=houses.angles.midheaven,
            planet_positions=positions,
            house_cusps=houses.house_cusps,
            aspects=aspects,
        )
