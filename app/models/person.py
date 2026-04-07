from __future__ import annotations

from dataclasses import dataclass


@dataclass(slots=True)
class Person:
    name: str
    notes: str = ""
    id: int | None = None
