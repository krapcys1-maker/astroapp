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


def _migration_003_charts(connection: sqlite3.Connection) -> None:
    connection.executescript(
        """
        CREATE TABLE IF NOT EXISTS charts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            person_id INTEGER NOT NULL,
            chart_type TEXT NOT NULL,
            house_system TEXT NOT NULL,
            zodiac_type TEXT NOT NULL,
            calculated_at TEXT NOT NULL,
            ascendant REAL,
            midheaven REAL,
            FOREIGN KEY (person_id) REFERENCES people(id) ON DELETE CASCADE
        );

        CREATE TABLE IF NOT EXISTS planet_positions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            chart_id INTEGER NOT NULL,
            body TEXT NOT NULL,
            longitude REAL NOT NULL,
            sign TEXT NOT NULL,
            degree_in_sign REAL NOT NULL,
            retrograde INTEGER NOT NULL,
            house INTEGER,
            FOREIGN KEY (chart_id) REFERENCES charts(id) ON DELETE CASCADE
        );

        CREATE TABLE IF NOT EXISTS house_cusps (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            chart_id INTEGER NOT NULL,
            house_number INTEGER NOT NULL,
            longitude REAL NOT NULL,
            FOREIGN KEY (chart_id) REFERENCES charts(id) ON DELETE CASCADE
        );

        CREATE TABLE IF NOT EXISTS aspects (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            chart_id INTEGER NOT NULL,
            body_a TEXT NOT NULL,
            body_b TEXT NOT NULL,
            aspect_type TEXT NOT NULL,
            orb REAL NOT NULL,
            phase TEXT NOT NULL,
            FOREIGN KEY (chart_id) REFERENCES charts(id) ON DELETE CASCADE
        );
        """
    )


def _migration_004_transit_queries(connection: sqlite3.Connection) -> None:
    connection.executescript(
        """
        CREATE TABLE IF NOT EXISTS transit_queries (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            person_id INTEGER NOT NULL,
            start_date TEXT NOT NULL,
            end_date TEXT NOT NULL,
            orb REAL NOT NULL,
            selected_transit_bodies TEXT NOT NULL,
            selected_natal_bodies TEXT NOT NULL,
            selected_aspects TEXT NOT NULL,
            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (person_id) REFERENCES people(id) ON DELETE CASCADE
        );
        """
    )


MIGRATIONS: dict[int, Migration] = {
    1: _migration_001_base,
    2: _migration_002_people_and_birth_data,
    3: _migration_003_charts,
    4: _migration_004_transit_queries,
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
