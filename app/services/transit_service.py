from __future__ import annotations

from datetime import UTC, datetime, time, timedelta
from pathlib import Path

from app.engine.ephemeris import EphemerisBackend
from app.engine.transit import AspectScanner, TransitPositionSampler
from app.models.aspect_event import AspectEvent
from app.models.chart import Chart
from app.models.planet_position import PlanetPosition
from app.models.transit_query import TransitQuery
from app.storage.repositories import ChartRepository, TransitQueryRepository
from app.utils.angle_utils import degree_in_sign, zodiac_sign


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
        self._queries = None if database_path is None else TransitQueryRepository(database_path)

    def search(
        self,
        query: TransitQuery,
        natal_chart: Chart | None = None,
    ) -> list[AspectEvent]:
        saved_query = self._save_query_if_possible(query)
        chart = natal_chart or self._get_required_natal_chart(query.person_id)
        window_start, window_end = self._window_for_query(saved_query)
        transit_bodies = saved_query.selected_transit_bodies or tuple(
            position.body for position in chart.planet_positions
        )
        samples = self._sampler.sample(window_start, window_end, transit_bodies)
        return self._scanner.scan(
            saved_query,
            chart,
            samples,
            window_start=window_start,
            window_end=window_end,
        )

    def list_recent_queries(
        self,
        *,
        person_id: int | None = None,
        limit: int = 10,
    ) -> list[TransitQuery]:
        if self._queries is None:
            return []
        return self._queries.list_recent(person_id=person_id, limit=limit)

    def calculate_positions(
        self,
        at_dt_utc: datetime,
        bodies: tuple[str, ...],
    ) -> list[PlanetPosition]:
        positions: list[PlanetPosition] = []
        for body in bodies:
            position = self._backend.get_planet_longitude(at_dt_utc, body)
            positions.append(
                PlanetPosition(
                    body=body,
                    longitude=position.longitude,
                    sign=zodiac_sign(position.longitude),
                    degree_in_sign=degree_in_sign(position.longitude),
                    retrograde=position.retrograde,
                    house=None,
                )
            )
        return positions

    def _get_required_natal_chart(self, person_id: int) -> Chart:
        if self._charts is None:
            msg = "Transit search requires a natal chart or a configured chart repository."
            raise LookupError(msg)
        chart = self._charts.get_latest_for_person(person_id)
        if chart is None:
            msg = f"No natal chart found for person_id={person_id}."
            raise LookupError(msg)
        return chart

    def _save_query_if_possible(self, query: TransitQuery) -> TransitQuery:
        if self._queries is None:
            return query
        return self._queries.save(query)

    @staticmethod
    def _window_for_query(query: TransitQuery) -> tuple[datetime, datetime]:
        start_dt = datetime.combine(query.start_date, time.min, tzinfo=UTC)
        end_dt = datetime.combine(
            query.end_date + timedelta(days=1),
            time.min,
            tzinfo=UTC,
        )
        return start_dt, end_dt
