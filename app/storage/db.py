from __future__ import annotations

import sqlite3
from pathlib import Path

from app.storage.migrations import LATEST_SCHEMA_VERSION, apply_migrations

SCHEMA_VERSION = LATEST_SCHEMA_VERSION


def connect_sqlite(database_path: Path) -> sqlite3.Connection:
    database_path.parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(database_path)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON")
    return connection


def initialize_database(database_path: Path) -> None:
    with connect_sqlite(database_path) as connection:
        apply_migrations(connection)
