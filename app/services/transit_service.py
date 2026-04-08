from __future__ import annotations

from collections.abc import Callable
from datetime import UTC, datetime, time, timedelta
from pathlib import Path

from app.engine.ephemeris import EphemerisBackend
from app.engine.natal.aspect_calculator import MAJOR_ASPECTS
from app.engine.transit import AspectScanner, TransitPositionSampler
from app.engine.transit.event_refiner import aspect_deviation
from app.models.aspect_event import AspectEvent
from app.models.birth_data import BirthData
from app.models.chart import Chart
from app.models.planet_position import PlanetPosition
from app.models.transit_aspect_hit import TransitAspectHit
from app.models.transit_query import TransitQuery
from app.storage.repositories import BirthDataRepository, ChartRepository, TransitQueryRepository
from app.utils.angle_utils import degree_in_sign, normalize_angle, zodiac_sign

ANGLE_BODIES = ("ASC", "DSC", "IC", "MC")


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
        self._birth_data = None if database_path is None else BirthDataRepository(database_path)

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
        longitude_resolver = self._build_longitude_resolver(
            person_id=query.person_id,
            house_system=chart.house_system,
            bodies=transit_bodies,
        )
        samples = self._sampler.sample(
            window_start,
            window_end,
            transit_bodies,
            longitude_resolver=longitude_resolver,
        )
        return self._scanner.scan(
            saved_query,
            chart,
            samples,
            window_start=window_start,
            window_end=window_end,
            longitude_resolver=longitude_resolver,
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

    def calculate_snapshot_aspects(
        self,
        *,
        at_dt_utc: datetime,
        natal_chart: Chart,
        orb: float = 3.0,
        transit_bodies: tuple[str, ...] | None = None,
        natal_bodies: tuple[str, ...] | None = None,
        aspect_types: tuple[str, ...] | None = None,
    ) -> list[TransitAspectHit]:
        selected_transit_bodies = transit_bodies or tuple(
            position.body for position in natal_chart.planet_positions
        )
        selected_natal_bodies = set(natal_bodies or ())
        selected_aspect_types = aspect_types or tuple(MAJOR_ASPECTS)
        transit_positions = {
            position.body: position
            for position in self.calculate_positions(at_dt_utc, selected_transit_bodies)
        }
        future_dt = at_dt_utc + timedelta(hours=1)
        future_positions = {
            position.body: position
            for position in self.calculate_positions(future_dt, selected_transit_bodies)
        }

        hits: list[TransitAspectHit] = []
        for natal_position in natal_chart.planet_positions:
            if selected_natal_bodies and natal_position.body not in selected_natal_bodies:
                continue
            for transit_body, transit_position in transit_positions.items():
                for aspect_type in selected_aspect_types:
                    current_orb = aspect_deviation(
                        transit_position.longitude,
                        natal_position.longitude,
                        aspect_type,
                    )
                    if current_orb > orb:
                        continue
                    future_orb = aspect_deviation(
                        future_positions[transit_body].longitude,
                        natal_position.longitude,
                        aspect_type,
                    )
                    if current_orb < 1e-3:
                        phase = "exact"
                    else:
                        phase = "applying" if future_orb < current_orb else "separating"
                    hits.append(
                        TransitAspectHit(
                            transit_body=transit_body,
                            natal_body=natal_position.body,
                            aspect_type=aspect_type,
                            orb=current_orb,
                            phase=phase,
                            at_dt=at_dt_utc,
                        )
                    )
                    break
        hits.sort(key=lambda item: (item.orb, item.transit_body, item.natal_body))
        return hits

    def _get_required_natal_chart(self, person_id: int) -> Chart:
        if self._charts is None:
            msg = "Transit search requires a natal chart or a configured chart repository."
            raise LookupError(msg)
        chart = self._charts.get_latest_for_person(person_id)
        if chart is None:
            msg = f"No natal chart found for person_id={person_id}."
            raise LookupError(msg)
        return chart

    def _get_required_birth_data(self, person_id: int) -> BirthData:
        if self._birth_data is None:
            msg = "Transit angles require configured birth data storage."
            raise LookupError(msg)
        birth_data = self._birth_data.get_by_person_id(person_id)
        if birth_data is None:
            msg = f"No birth data found for person_id={person_id}."
            raise LookupError(msg)
        return birth_data

    def _build_longitude_resolver(
        self,
        *,
        person_id: int,
        house_system: str,
        bodies: tuple[str, ...],
    ) -> Callable[[datetime, str], float]:
        if not any(body in ANGLE_BODIES for body in bodies):
            return (
                lambda at_dt_utc, body: self._backend.get_planet_longitude(
                    at_dt_utc,
                    body,
                ).longitude
            )

        birth_data = self._get_required_birth_data(person_id)
        angle_cache: dict[datetime, dict[str, float]] = {}

        def resolver(at_dt_utc: datetime, body: str) -> float:
            if body not in ANGLE_BODIES:
                return self._backend.get_planet_longitude(at_dt_utc, body).longitude
            if at_dt_utc not in angle_cache:
                angles = self._backend.get_angles(
                    at_dt_utc,
                    birth_data.latitude,
                    birth_data.longitude,
                    house_system,
                )
                ascendant = normalize_angle(angles.ascendant)
                midheaven = normalize_angle(angles.midheaven)
                angle_cache[at_dt_utc] = {
                    "ASC": ascendant,
                    "DSC": normalize_angle(ascendant + 180.0),
                    "MC": midheaven,
                    "IC": normalize_angle(midheaven + 180.0),
                }
            return angle_cache[at_dt_utc][body]

        return resolver

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
