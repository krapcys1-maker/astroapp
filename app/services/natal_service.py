from __future__ import annotations

from app.engine.ephemeris import EphemerisBackend
from app.engine.natal.aspect_calculator import AspectCalculator
from app.engine.natal.chart_calculator import ChartCalculator
from app.engine.natal.house_calculator import HouseCalculator
from app.models.birth_data import BirthData
from app.models.chart import Chart
from app.models.chart_settings import NatalChartSettings


class NatalService:
    def __init__(self, backend: EphemerisBackend) -> None:
        self._calculator = ChartCalculator(
            backend=backend,
            house_calculator=HouseCalculator(backend),
            aspect_calculator=AspectCalculator(),
        )

    def calculate_chart(
        self,
        *,
        person_id: int,
        birth_data: BirthData,
        settings: NatalChartSettings | None = None,
    ) -> Chart:
        return self._calculator.calculate(
            birth_data=birth_data,
            settings=settings or NatalChartSettings(),
            person_id=person_id,
        )
