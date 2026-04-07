from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Protocol, runtime_checkable


def normalize_longitude(value: float) -> float:
    normalized = value % 360.0
    if normalized < 0:
        normalized += 360.0
    return normalized


def require_utc_datetime(value: datetime) -> datetime:
    if value.tzinfo is None or value.utcoffset() is None:
        msg = "Expected an aware datetime."
        raise ValueError(msg)
    return value.astimezone(UTC)


@dataclass(slots=True, frozen=True)
class PlanetLongitude:
    body: str
    longitude: float
    latitude: float
    distance_au: float
    speed_longitude: float
    retflag: int

    @property
    def retrograde(self) -> bool:
        return self.speed_longitude < 0


@dataclass(slots=True, frozen=True)
class HouseCusps:
    house_system: str
    cusps: tuple[float, ...]

    def __post_init__(self) -> None:
        if len(self.cusps) != 12:
            msg = "House cusps must contain exactly 12 values."
            raise ValueError(msg)


@dataclass(slots=True, frozen=True)
class ChartAngles:
    ascendant: float
    midheaven: float


@runtime_checkable
class EphemerisBackend(Protocol):
    def get_planet_longitude(self, dt_utc: datetime, body: str) -> PlanetLongitude:
        ...

    def get_house_cusps(
        self,
        dt_utc: datetime,
        lat: float,
        lon: float,
        house_system: str,
    ) -> HouseCusps:
        ...

    def get_angles(
        self,
        dt_utc: datetime,
        lat: float,
        lon: float,
        house_system: str,
    ) -> ChartAngles:
        ...
