from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from datetime import datetime

from app.engine.ephemeris import EphemerisBackend
from app.engine.natal.aspect_calculator import MAJOR_ASPECTS
from app.engine.transit.event_refiner import EventRefiner, in_orb
from app.engine.transit.transit_position_sampler import TransitSample
from app.models.aspect_event import AspectEvent
from app.models.chart import Chart
from app.models.transit_query import TransitQuery


@dataclass(slots=True, frozen=True)
class NatalPoint:
    body: str
    longitude: float


class AspectScanner:
    def __init__(
        self,
        backend: EphemerisBackend,
        refiner: EventRefiner | None = None,
    ) -> None:
        self._backend = backend
        self._refiner = refiner or EventRefiner()

    def scan(
        self,
        query: TransitQuery,
        natal_chart: Chart,
        samples: list[TransitSample],
        *,
        window_start: datetime,
        window_end: datetime,
        longitude_resolver: Callable[[datetime, str], float] | None = None,
    ) -> list[AspectEvent]:
        natal_points = self._select_natal_points(query, natal_chart)
        transit_bodies = query.selected_transit_bodies or tuple(
            point.body for point in natal_chart.planet_positions
        )
        aspects = query.selected_aspects or tuple(MAJOR_ASPECTS)
        events: list[AspectEvent] = []

        for transit_body in transit_bodies:
            for natal_point in natal_points:
                for aspect_type in aspects:
                    events.extend(
                        self._scan_single_series(
                            query=query,
                            transit_body=transit_body,
                            natal_point=natal_point,
                            aspect_type=aspect_type,
                            samples=samples,
                            window_start=window_start,
                            window_end=window_end,
                            longitude_resolver=longitude_resolver,
                        )
                    )
        return events

    def _scan_single_series(
        self,
        *,
        query: TransitQuery,
        transit_body: str,
        natal_point: NatalPoint,
        aspect_type: str,
        samples: list[TransitSample],
        window_start: datetime,
        window_end: datetime,
        longitude_resolver: Callable[[datetime, str], float] | None,
    ) -> list[AspectEvent]:
        if not samples:
            return []

        def longitude_at(dt: datetime) -> float:
            if longitude_resolver is not None:
                return longitude_resolver(dt, transit_body)
            return self._backend.get_planet_longitude(dt, transit_body).longitude

        def state_at(dt: datetime) -> bool:
            return in_orb(
                longitude_at(dt),
                natal_point.longitude,
                aspect_type,
                query.orb,
            )

        events: list[AspectEvent] = []
        currently_in_orb = in_orb(
            samples[0].positions[transit_body],
            natal_point.longitude,
            aspect_type,
            query.orb,
        )
        event_start = window_start if currently_in_orb else None

        for previous, current in zip(samples, samples[1:], strict=False):
            previous_state = in_orb(
                previous.positions[transit_body],
                natal_point.longitude,
                aspect_type,
                query.orb,
            )
            current_state = in_orb(
                current.positions[transit_body],
                natal_point.longitude,
                aspect_type,
                query.orb,
            )

            if not previous_state and current_state:
                event_start = self._refiner.refine_boundary(
                    previous.timestamp,
                    current.timestamp,
                    state_at,
                    expected_state_at_end=True,
                )
                currently_in_orb = True
                continue

            if previous_state and not current_state and event_start is not None:
                event_end = self._refiner.refine_boundary(
                    previous.timestamp,
                    current.timestamp,
                    state_at,
                    expected_state_at_end=False,
                )
                refined = self._refiner.refine_exact(
                    event_start,
                    event_end,
                    longitude_at,
                    natal_point.longitude,
                    aspect_type,
                )
                events.append(
                    AspectEvent(
                        transit_body=transit_body,
                        natal_body=natal_point.body,
                        aspect_type=aspect_type,
                        start_dt=event_start,
                        exact_dt=refined.exact_dt,
                        end_dt=event_end,
                        exact_orb=refined.exact_orb,
                        phase=refined.phase,
                        query_id=query.id,
                    )
                )
                event_start = None
                currently_in_orb = False

        if currently_in_orb and event_start is not None:
            refined = self._refiner.refine_exact(
                event_start,
                window_end,
                longitude_at,
                natal_point.longitude,
                aspect_type,
            )
            events.append(
                AspectEvent(
                    transit_body=transit_body,
                    natal_body=natal_point.body,
                    aspect_type=aspect_type,
                    start_dt=event_start,
                    exact_dt=refined.exact_dt,
                    end_dt=None,
                    exact_orb=refined.exact_orb,
                    phase=refined.phase,
                    query_id=query.id,
                )
            )

        return events

    @staticmethod
    def _select_natal_points(query: TransitQuery, natal_chart: Chart) -> list[NatalPoint]:
        allowed = set(query.selected_natal_bodies)
        points = [
            NatalPoint(body=position.body, longitude=position.longitude)
            for position in natal_chart.planet_positions
            if not allowed or position.body in allowed
        ]
        ascendant = natal_chart.ascendant
        midheaven = natal_chart.midheaven
        if ascendant is not None and midheaven is not None:
            extra_points = [
                NatalPoint(body="ASC", longitude=ascendant),
                NatalPoint(body="DSC", longitude=(ascendant + 180.0) % 360.0),
                NatalPoint(body="MC", longitude=midheaven),
                NatalPoint(body="IC", longitude=(midheaven + 180.0) % 360.0),
            ]
            points.extend(
                point
                for point in extra_points
                if not allowed or point.body in allowed
            )
        return points
