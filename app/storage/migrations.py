from __future__ import annotations

import sqlite3
from collections.abc import Callable

Migration = Callable[[sqlite3.Connection], None]


def ensure_core_tables(connection: sqlite3.Connection) -> None:
    connection.executescript(
        """
        CREATE TABLE IF NOT EXISTS schema_migrations (
            version INTEGER PRIMARY KEY,
            applied_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS app_metadata (
            key TEXT PRIMARY KEY,
            value TEXT NOT NULL
        );
        """
    )


def _migration_001_base(_: sqlite3.Connection) -> None:
    """Reserve the initial schema version for the project bootstrap."""


def _migration_002_people_and_birth_data(connection: sqlite3.Connection) -> None:
    connection.executescript(
        """
        CREATE TABLE IF NOT EXISTS people (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            notes TEXT NOT NULL DEFAULT ''
        );

        CREATE TABLE IF NOT EXISTS birth_data (
            person_id INTEGER PRIMARY KEY,
            birth_date TEXT NOT NULL,
            birth_time TEXT NOT NULL,
            city TEXT NOT NULL,
            country TEXT NOT NULL,
            latitude REAL NOT NULL,
            longitude REAL NOT NULL,
            timezone_name TEXT NOT NULL,
            FOREIGN KEY (person_id) REFERENCES people(id) ON DELETE CASCADE
        );
        """
    )


MIGRATIONS: dict[int, Migration] = {
    1: _migration_001_base,
    2: _migration_002_people_and_birth_data,
}

LATEST_SCHEMA_VERSION = max(MIGRATIONS)


def apply_migrations(connection: sqlite3.Connection) -> None:
    ensure_core_tables(connection)
    applied_versions = {
        row[0]
        for row in connection.execute("SELECT version FROM schema_migrations").fetchall()
    }
    for version, migration in sorted(MIGRATIONS.items()):
        if version in applied_versions:
            continue
        migration(connection)
        connection.execute(
            "INSERT INTO schema_migrations(version) VALUES (?)",
            (version,),
        )
    connection.execute(
        """
        INSERT INTO app_metadata(key, value)
        VALUES ('schema_version', ?)
        ON CONFLICT(key) DO UPDATE SET value = excluded.value
        """,
        (str(LATEST_SCHEMA_VERSION),),
    )
