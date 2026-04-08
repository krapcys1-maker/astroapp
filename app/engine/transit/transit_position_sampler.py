from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from datetime import datetime, timedelta

from app.engine.ephemeris import EphemerisBackend


@dataclass(slots=True, frozen=True)
class TransitSample:
    timestamp: datetime
    positions: dict[str, float]


class TransitPositionSampler:
    def __init__(
        self,
        backend: EphemerisBackend,
        step: timedelta = timedelta(hours=6),
    ) -> None:
        self._backend = backend
        self._step = step

    def sample(
        self,
        start_dt: datetime,
        end_dt: datetime,
        bodies: tuple[str, ...],
        *,
        longitude_resolver: Callable[[datetime, str], float] | None = None,
    ) -> list[TransitSample]:
        samples: list[TransitSample] = []
        cursor = start_dt
        resolver = longitude_resolver or (
            lambda timestamp, body: self._backend.get_planet_longitude(timestamp, body).longitude
        )
        while cursor <= end_dt:
            samples.append(
                TransitSample(
                    timestamp=cursor,
                    positions={
                        body: resolver(cursor, body)
                        for body in bodies
                    },
                )
            )
            if cursor == end_dt:
                break
            cursor = min(cursor + self._step, end_dt)
        return samples
