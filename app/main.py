from __future__ import annotations

import sys

from PySide6.QtWidgets import QApplication

from app.config.settings import AppSettings
from app.engine.ephemeris import SwissEphemerisBackend
from app.services import NatalService, PersonService, TransitService
from app.storage.db import initialize_database
from app.ui.main_window import MainWindow


def create_application() -> QApplication:
    app = QApplication.instance()
    if app is None:
        app = QApplication(sys.argv)
    app.setStyle("Fusion")
    app.setApplicationName("astroapp")
    app.setOrganizationName("astroapp")
    return app


def main() -> int:
    settings = AppSettings.from_environment()
    settings.ensure_directories()
    initialize_database(settings.database_path)
    person_service = PersonService(settings.database_path)
    natal_service = None
    transit_service = None
    natal_error = None
    try:
        backend = SwissEphemerisBackend(settings.ephemeris_path)
        natal_service = NatalService(backend, database_path=settings.database_path)
        transit_service = TransitService(backend, database_path=settings.database_path)
    except RuntimeError as exc:
        natal_error = str(exc)
    application = create_application()
    window = MainWindow(
        settings=settings,
        person_service=person_service,
        natal_service=natal_service,
        transit_service=transit_service,
        natal_error=natal_error,
        transit_error=natal_error,
    )
    window.show()
    return application.exec()


if __name__ == "__main__":
    raise SystemExit(main())
