from __future__ import annotations

import importlib
from datetime import datetime
from pathlib import Path
from typing import Any

from app.engine.ephemeris.backend import (
    ChartAngles,
    HouseCusps,
    PlanetLongitude,
    normalize_longitude,
    require_utc_datetime,
)

BODY_CODES = {
    "sun": "SUN",
    "moon": "MOON",
    "mercury": "MERCURY",
    "venus": "VENUS",
    "mars": "MARS",
    "jupiter": "JUPITER",
    "saturn": "SATURN",
    "uranus": "URANUS",
    "neptune": "NEPTUNE",
    "pluto": "PLUTO",
}

HOUSE_SYSTEM_CODES = {
    "P": "P",
    "PLACIDUS": "P",
    "K": "K",
    "KOCH": "K",
    "W": "W",
    "WHOLE_SIGN": "W",
    "WHOLESIGN": "W",
    "E": "E",
    "EQUAL": "E",
}


def _load_swiss_module() -> Any:
    try:
        return importlib.import_module("swisseph")
    except ModuleNotFoundError as exc:
        msg = (
            "Swiss Ephemeris support requires the optional 'astro' dependencies. "
            "Install them with 'pip install -e .[astro]'."
        )
        raise RuntimeError(msg) from exc


def _julian_day(swe_module: Any, dt_utc: datetime) -> float:
    utc_dt = require_utc_datetime(dt_utc)
    hour = utc_dt.hour + (utc_dt.minute / 60) + (utc_dt.second / 3600)
    hour += utc_dt.microsecond / 3_600_000_000
    return swe_module.julday(
        utc_dt.year,
        utc_dt.month,
        utc_dt.day,
        hour,
    )


def _normalize_house_system(house_system: str) -> bytes:
    normalized = house_system.strip().upper()
    code = HOUSE_SYSTEM_CODES.get(normalized)
    if code is None:
        msg = f"Unsupported house system: {house_system}"
        raise ValueError(msg)
    return code.encode("ascii")


def _unpack_calc_result(result: Any) -> tuple[tuple[float, ...] | list[float], int]:
    if not isinstance(result, tuple):
        msg = "Swiss Ephemeris returned an unexpected calc_ut payload."
        raise ValueError(msg)
    if len(result) == 2:
        values, retflag = result
        return values, int(retflag)
    if len(result) == 3:
        values, retflag, _message = result
        return values, int(retflag)
    msg = "Swiss Ephemeris returned an unexpected calc_ut payload."
    raise ValueError(msg)


def _extract_house_cusps(raw_cusps: tuple[float, ...] | list[float]) -> tuple[float, ...]:
    if len(raw_cusps) == 13:
        relevant = raw_cusps[1:13]
    elif len(raw_cusps) == 12:
        relevant = raw_cusps
    else:
        msg = "Swiss Ephemeris returned an unexpected number of house cusps."
        raise ValueError(msg)
    return tuple(normalize_longitude(value) for value in relevant)


class SwissEphemerisBackend:
    def __init__(self, ephemeris_path: Path, swe_module: Any | None = None) -> None:
        self._ephemeris_path = Path(ephemeris_path)
        self._swe = swe_module or _load_swiss_module()
        self._swe.set_ephe_path(str(self._ephemeris_path))
        self._planet_flags = self._swe.FLG_SWIEPH | self._swe.FLG_SPEED
        self._house_flags = self._swe.FLG_SWIEPH

    def get_planet_longitude(self, dt_utc: datetime, body: str) -> PlanetLongitude:
        body_code_name = BODY_CODES.get(body.strip().lower())
        if body_code_name is None:
            msg = f"Unsupported Swiss Ephemeris body: {body}"
            raise ValueError(msg)

        julian_day = _julian_day(self._swe, dt_utc)
        body_code = getattr(self._swe, body_code_name)
        values, retflag = _unpack_calc_result(
            self._swe.calc_ut(julian_day, body_code, self._planet_flags)
        )
        return PlanetLongitude(
            body=body,
            longitude=normalize_longitude(values[0]),
            latitude=values[1],
            distance_au=values[2],
            speed_longitude=values[3],
            retflag=retflag,
        )

    def get_house_cusps(
        self,
        dt_utc: datetime,
        lat: float,
        lon: float,
        house_system: str,
    ) -> HouseCusps:
        julian_day = _julian_day(self._swe, dt_utc)
        cusps, _ascmc = self._swe.houses_ex(
            julian_day,
            lat,
            lon,
            _normalize_house_system(house_system),
            self._house_flags,
        )
        return HouseCusps(
            house_system=house_system.strip().upper(),
            cusps=_extract_house_cusps(cusps),
        )

    def get_angles(
        self,
        dt_utc: datetime,
        lat: float,
        lon: float,
        house_system: str,
    ) -> ChartAngles:
        julian_day = _julian_day(self._swe, dt_utc)
        _cusps, ascmc = self._swe.houses_ex(
            julian_day,
            lat,
            lon,
            _normalize_house_system(house_system),
            self._house_flags,
        )
        return ChartAngles(
            ascendant=normalize_longitude(ascmc[0]),
            midheaven=normalize_longitude(ascmc[1]),
        )
