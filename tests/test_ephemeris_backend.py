from __future__ import annotations

from datetime import UTC, datetime, timedelta, timezone
from pathlib import Path

import pytest

from app.engine.ephemeris import EphemerisBackend, normalize_longitude, require_utc_datetime
from app.engine.ephemeris.backend import HouseCusps, PlanetLongitude
from app.engine.ephemeris.swiss_ephemeris_backend import (
    SwissEphemerisBackend,
    _load_swiss_module,
    _unpack_calc_result,
)


class FakeSwissModule:
    FLG_SWIEPH = 2
    FLG_SPEED = 256
    SUN = 0

    def __init__(self) -> None:
        self.ephe_path: str | None = None
        self.last_julday: tuple[int, int, int, float] | None = None
        self.calc_calls: list[tuple[float, int, int]] = []
        self.house_calls: list[tuple[float, float, float, bytes, int]] = []

    def set_ephe_path(self, path: str) -> None:
        self.ephe_path = path

    def julday(self, year: int, month: int, day: int, hour: float) -> float:
        self.last_julday = (year, month, day, hour)
        return 2_460_000.5 + hour

    def calc_ut(self, julian_day: float, body: int, flags: int) -> tuple[list[float], int]:
        self.calc_calls.append((julian_day, body, flags))
        return [361.5, -1.25, 0.99, -0.05, 0.0, 0.0], 260

    def houses_ex(
        self,
        julian_day: float,
        lat: float,
        lon: float,
        house_system: bytes,
        flags: int,
    ) -> tuple[list[float], list[float]]:
        self.house_calls.append((julian_day, lat, lon, house_system, flags))
        return (
            [0.0, 10.0, 40.0, 70.0, 100.0, 130.0, 160.0, 190.0, 220.0, 250.0, 280.0, 310.0, 340.0],
            [725.0, -15.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0],
        )


def test_normalize_longitude_wraps_values() -> None:
    assert normalize_longitude(361.5) == pytest.approx(1.5)
    assert normalize_longitude(-15.0) == pytest.approx(345.0)


def test_require_utc_datetime_rejects_naive_values() -> None:
    with pytest.raises(ValueError):
        require_utc_datetime(datetime(2026, 1, 1, 12, 0, 0))


def test_require_utc_datetime_converts_to_utc() -> None:
    local = datetime(2026, 1, 1, 14, 0, 0, tzinfo=timezone(timedelta(hours=2)))

    utc_value = require_utc_datetime(local)

    assert utc_value.tzinfo == UTC
    assert utc_value.hour == 12


def test_house_cusps_validate_length() -> None:
    with pytest.raises(ValueError):
        HouseCusps(house_system="P", cusps=(10.0, 20.0))


def test_planet_longitude_reports_retrograde() -> None:
    position = PlanetLongitude(
        body="Sun",
        longitude=10.0,
        latitude=0.0,
        distance_au=1.0,
        speed_longitude=-0.1,
        retflag=0,
    )

    assert position.retrograde is True


def test_swiss_backend_matches_protocol_and_sets_ephemeris_path(tmp_path: Path) -> None:
    fake = FakeSwissModule()
    backend = SwissEphemerisBackend(tmp_path / "ephemeris", swe_module=fake)

    assert isinstance(backend, EphemerisBackend)
    assert fake.ephe_path == str(tmp_path / "ephemeris")


def test_swiss_backend_returns_normalized_planet_position(tmp_path: Path) -> None:
    fake = FakeSwissModule()
    backend = SwissEphemerisBackend(tmp_path / "ephemeris", swe_module=fake)

    position = backend.get_planet_longitude(
        datetime(2026, 4, 7, 14, 30, tzinfo=UTC),
        "Sun",
    )

    assert position.longitude == pytest.approx(1.5)
    assert position.retrograde is True
    assert fake.calc_calls


def test_swiss_backend_returns_house_cusps_and_angles(tmp_path: Path) -> None:
    fake = FakeSwissModule()
    backend = SwissEphemerisBackend(tmp_path / "ephemeris", swe_module=fake)

    cusps = backend.get_house_cusps(
        datetime(2026, 4, 7, 14, 30, tzinfo=UTC),
        lat=52.2297,
        lon=21.0122,
        house_system="Placidus",
    )
    angles = backend.get_angles(
        datetime(2026, 4, 7, 14, 30, tzinfo=UTC),
        lat=52.2297,
        lon=21.0122,
        house_system="Placidus",
    )

    assert len(cusps.cusps) == 12
    assert cusps.cusps[0] == pytest.approx(10.0)
    assert angles.ascendant == pytest.approx(5.0)
    assert angles.midheaven == pytest.approx(345.0)
    assert fake.house_calls[0][3] == b"P"


def test_swiss_backend_rejects_unsupported_values(tmp_path: Path) -> None:
    fake = FakeSwissModule()
    backend = SwissEphemerisBackend(tmp_path / "ephemeris", swe_module=fake)

    with pytest.raises(ValueError):
        backend.get_planet_longitude(
            datetime(2026, 4, 7, 14, 30, tzinfo=UTC),
            "Ceres",
        )

    with pytest.raises(ValueError):
        backend.get_house_cusps(
            datetime(2026, 4, 7, 14, 30, tzinfo=UTC),
            lat=52.2297,
            lon=21.0122,
            house_system="Placidus Extended",
        )


def test_loading_swiss_module_without_dependency_raises_helpful_error(monkeypatch) -> None:
    def _missing_module(_: str) -> None:
        raise ModuleNotFoundError("swisseph")

    monkeypatch.setattr("importlib.import_module", _missing_module)

    with pytest.raises(RuntimeError, match="pip install -e .\\[astro\\]"):
        _load_swiss_module()


def test_unpack_calc_result_accepts_real_pysweph_shape() -> None:
    values, retflag = _unpack_calc_result(([1.0, 2.0, 3.0], 260, "fallback"))

    assert values == [1.0, 2.0, 3.0]
    assert retflag == 260
