from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


def _default_data_dir() -> Path:
    return Path.cwd() / ".astroapp"


@dataclass(slots=True, frozen=True)
class AppSettings:
    app_name: str
    data_dir: Path
    database_path: Path
    ephemeris_path: Path

    @classmethod
    def from_environment(cls) -> AppSettings:
        data_dir = _default_data_dir()
        return cls(
            app_name="astroapp",
            data_dir=data_dir,
            database_path=data_dir / "astroapp.sqlite3",
            ephemeris_path=data_dir / "ephemeris",
        )
