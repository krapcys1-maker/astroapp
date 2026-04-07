from __future__ import annotations

from datetime import UTC, datetime, time, timedelta
from pathlib import Path

from app.engine.ephemeris import EphemerisBackend
from app.engine.transit import AspectScanner, TransitPositionSampler
from app.models.aspect_event import AspectEvent
from app.models.chart import Chart
from app.models.transit_query import TransitQuery
from app.storage.repositories import ChartRepository


class TransitService:
    def __init__(
        self,
        backend: EphemerisBackend,
        database_path: Path | None = None,
    ) -> None:
        self._backend = backend
        self._sampler = TransitPositionSampler(backend)
        self._scanner = AspectScanner(backend)
        self._charts = None if database_path is None else ChartRepository(database_path)

    def search(
        self,
        query: TransitQuery,
        natal_chart: Chart | None = None,
    ) -> list[AspectEvent]:
        chart = natal_chart or self._get_required_natal_chart(query.person_id)
        window_start, window_end = self._window_for_query(query)
        transit_bodies = query.selected_transit_bodies or tuple(
            position.body for position in chart.planet_positions
        )
        samples = self._sampler.sample(window_start, window_end, transit_bodies)
        return self._scanner.scan(
            query,
            chart,
            samples,
            window_start=window_start,
            window_end=window_end,
        )

    def _get_required_natal_chart(self, person_id: int) -> Chart:
        if self._charts is None:
            msg = "Transit search requires a natal chart or a configured chart repository."
            raise LookupError(msg)
        chart = self._charts.get_latest_for_person(person_id)
        if chart is None:
            msg = f"No natal chart found for person_id={person_id}."
            raise LookupError(msg)
        return chart

    @staticmethod
    def _window_for_query(query: TransitQuery) -> tuple[datetime, datetime]:
        start_dt = datetime.combine(query.start_date, time.min, tzinfo=UTC)
        end_dt = datetime.combine(
            query.end_date + timedelta(days=1),
            time.min,
            tzinfo=UTC,
        )
        return start_dt, end_dt
