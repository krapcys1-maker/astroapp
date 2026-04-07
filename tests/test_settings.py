from __future__ import annotations

from app.config.settings import AppSettings


def test_app_settings_use_expected_paths() -> None:
    settings = AppSettings.from_environment()

    assert settings.app_name == "astroapp"
    assert settings.database_path.name == "astroapp.sqlite3"
    assert settings.ephemeris_path.name == "ephemeris"