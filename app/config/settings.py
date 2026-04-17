from __future__ import annotations

import os
import shutil
import sys
from dataclasses import dataclass
from pathlib import Path

from app.config.runtime_paths import bundled_resource_path


def _default_data_dir() -> Path:
    if os.name == "nt":
        base_dir = Path(os.getenv("LOCALAPPDATA", Path.home() / "AppData" / "Local"))
        return base_dir / "AstroLabb"
    if sys.platform == "darwin":
        return Path.home() / "Library" / "Application Support" / "AstroLabb"
    base_dir = Path(os.getenv("XDG_DATA_HOME", Path.home() / ".local" / "share"))
    return base_dir / "astroapp"


def _path_from_env(name: str, default: Path) -> Path:
    raw_value = os.getenv(name)
    if not raw_value:
        return default
    return Path(raw_value).expanduser()


def _copy_tree_contents(source_dir: Path, target_dir: Path) -> None:
    for source_path in source_dir.rglob("*"):
        relative_path = source_path.relative_to(source_dir)
        target_path = target_dir / relative_path
        if source_path.is_dir():
            target_path.mkdir(parents=True, exist_ok=True)
            continue
        target_path.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source_path, target_path)


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
        self.database_path.parent.mkdir(parents=True, exist_ok=True)
        self.ephemeris_path.mkdir(parents=True, exist_ok=True)
        bundled_ephemeris_dir = bundled_resource_path("ephemeris")
        if bundled_ephemeris_dir.exists():
            _copy_tree_contents(bundled_ephemeris_dir, self.ephemeris_path)
