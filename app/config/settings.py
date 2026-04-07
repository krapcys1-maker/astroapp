from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path


def _default_data_dir() -> Path:
    return Path.cwd() / ".astroapp"


def _path_from_env(name: str, default: Path) -> Path:
    raw_value = os.getenv(name)
    if not raw_value:
        return default
    return Path(raw_value).expanduser()


@dataclass(slots=True, frozen=True)
class AppSettings:
    app_name: str
    data_dir: Path
    database_path: Path
    ephemeris_path: Path

    @classmethod
    def from_environment(cls) -> AppSettings:
        data_dir = _path_from_env("ASTROAPP_DATA_DIR", _default_data_dir())
        return cls(
            app_name="astroapp",
            data_dir=data_dir,
            database_path=_path_from_env(
                "ASTROAPP_DATABASE_PATH",
                data_dir / "astroapp.sqlite3",
            ),
            ephemeris_path=_path_from_env(
                "ASTROAPP_EPHEMERIS_PATH",
                data_dir / "ephemeris",
            ),
        )

    def ensure_directories(self) -> None:
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.ephemeris_path.mkdir(parents=True, exist_ok=True)
