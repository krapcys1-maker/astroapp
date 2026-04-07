from __future__ import annotations

import pytest

from app.config.settings import AppSettings
from app.services.person_service import PersonService
from app.storage.db import initialize_database

pytestmark = pytest.mark.ui


def test_main_window_smoke(tmp_path) -> None:
    from app.main import create_application
    from app.ui.main_window import MainWindow

    application = create_application()
    settings = AppSettings.from_environment()
    database_path = tmp_path / "smoke.sqlite3"
    initialize_database(database_path)
    person_service = PersonService(database_path)
    window = MainWindow(
        settings=settings,
        person_service=person_service,
        natal_service=None,
        transit_service=None,
        natal_error="Swiss backend unavailable in smoke test.",
        transit_error="Swiss backend unavailable in smoke test.",
    )

    assert application.applicationName() == "astroapp"
    assert window.windowTitle() == "astroapp"
    assert window.centralWidget() is not None
