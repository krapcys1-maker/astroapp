from __future__ import annotations

from app.config.settings import AppSettings
from app.main import create_application
from app.ui.main_window import MainWindow


def test_main_window_smoke() -> None:
    application = create_application()
    window = MainWindow(settings=AppSettings.from_environment())

    assert application.applicationName() == "astroapp"
    assert window.windowTitle() == "astroapp"
    assert window.centralWidget() is not None