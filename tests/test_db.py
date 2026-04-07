from __future__ import annotations

import sqlite3
from pathlib import Path

from app.storage.db import SCHEMA_VERSION, connect_sqlite, initialize_database


def test_initialize_database_creates_bootstrap_tables(tmp_path: Path) -> None:
    database_path = tmp_path / "test.sqlite3"

    initialize_database(database_path)

    with sqlite3.connect(database_path) as connection:
        tables = {
            row[0]
            for row in connection.execute(
                "SELECT name FROM sqlite_master WHERE type = 'table'"
            ).fetchall()
        }
        schema_version = connection.execute(
            "SELECT value FROM app_metadata WHERE key = 'schema_version'"
        ).fetchone()

    assert "schema_migrations" in tables
    assert "app_metadata" in tables
    assert "people" in tables
    assert "birth_data" in tables
    assert schema_version == (str(SCHEMA_VERSION),)


def test_connect_sqlite_enables_row_factory(tmp_path: Path) -> None:
    database_path = tmp_path / "row_factory.sqlite3"

    with connect_sqlite(database_path) as connection:
        connection.execute("CREATE TABLE sample (name TEXT NOT NULL)")
        connection.execute("INSERT INTO sample(name) VALUES ('astroapp')")
        row = connection.execute("SELECT name FROM sample").fetchone()

    assert row["name"] == "astroapp"
