from __future__ import annotations

from pathlib import Path

from app.config.settings import AppSettings, _copy_tree_contents


def test_app_settings_use_expected_paths() -> None:
    settings = AppSettings.from_environment()

    assert settings.app_name == "astroapp"
    assert settings.database_path.name == "astroapp.sqlite3"
    assert settings.ephemeris_path.name == "ephemeris"


def test_app_settings_support_environment_overrides(
    monkeypatch,
    tmp_path: Path,
) -> None:
    data_dir = tmp_path / "custom-data"
    database_path = tmp_path / "db" / "custom.sqlite3"
    ephemeris_path = tmp_path / "eph"

    monkeypatch.setenv("ASTROAPP_DATA_DIR", str(data_dir))
    monkeypatch.setenv("ASTROAPP_DATABASE_PATH", str(database_path))
    monkeypatch.setenv("ASTROAPP_EPHEMERIS_PATH", str(ephemeris_path))

    settings = AppSettings.from_environment()
    settings.ensure_directories()

    assert settings.data_dir == data_dir
    assert settings.database_path == database_path
    assert settings.ephemeris_path == ephemeris_path
    assert data_dir.exists()
    assert database_path.parent.exists()
    assert ephemeris_path.exists()


def test_copy_tree_contents_copies_nested_files(tmp_path: Path) -> None:
    source_dir = tmp_path / "source"
    target_dir = tmp_path / "target"
    nested_source = source_dir / "ast90"
    nested_source.mkdir(parents=True)
    (source_dir / "seas_18.se1").write_text("root", encoding="utf-8")
    (nested_source / "se90377s.se1").write_text("nested", encoding="utf-8")

    _copy_tree_contents(source_dir, target_dir)

    assert (target_dir / "seas_18.se1").read_text(encoding="utf-8") == "root"
    assert (target_dir / "ast90" / "se90377s.se1").read_text(encoding="utf-8") == "nested"
