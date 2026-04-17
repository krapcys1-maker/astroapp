from __future__ import annotations

import sys
from pathlib import Path


def application_root() -> Path:
    if getattr(sys, "frozen", False):
        meipass = getattr(sys, "_MEIPASS", None)
        if meipass:
            return Path(meipass)
        return Path(sys.executable).resolve().parent
    return Path(__file__).resolve().parents[2]


def bundled_resource_path(*parts: str) -> Path:
    root = application_root()
    bundled_root = root / "resources"
    if bundled_root.exists():
        return bundled_root.joinpath(*parts)
    return (root / "app" / "resources").joinpath(*parts)
