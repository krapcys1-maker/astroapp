from __future__ import annotations

from pathlib import Path

from app.engine.ephemeris import EphemerisBackend
from app.engine.natal.aspect_calculator import AspectCalculator
from app.engine.natal.chart_calculator import ChartCalculator
from app.engine.natal.house_calculator import HouseCalculator
from app.models.birth_data import BirthData
from app.models.chart import Chart
from app.models.chart_settings import NatalChartSettings
from app.storage.repositories import ChartRepository


class NatalService:
    def __init__(
        self,
        backend: EphemerisBackend,
        database_path: Path | None = None,
    ) -> None:
        self._calculator = ChartCalculator(
            backend=backend,
            house_calculator=HouseCalculator(backend),
            aspect_calculator=AspectCalculator(),
        )
        self._charts = None if database_path is None else ChartRepository(database_path)

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

    def calculate_and_save_chart(
        self,
        *,
        person_id: int,
        birth_data: BirthData,
        settings: NatalChartSettings | None = None,
    ) -> Chart:
        chart = self.calculate_chart(
            person_id=person_id,
            birth_data=birth_data,
            settings=settings,
        )
        if self._charts is None:
            return chart
        return self._charts.save(chart)

    def get_latest_chart(self, person_id: int) -> Chart | None:
        if self._charts is None:
            return None
        return self._charts.get_latest_for_person(person_id)
