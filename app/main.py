from __future__ import annotations

import sys

from PySide6.QtWidgets import QApplication

from app.config.settings import AppSettings
from app.storage.db import initialize_database
from app.ui.main_window import MainWindow


def create_application() -> QApplication:
    app = QApplication.instance()
    if app is None:
        app = QApplication(sys.argv)
    app.setApplicationName("astroapp")
    app.setOrganizationName("astroapp")
    return app


def main() -> int:
    settings = AppSettings.from_environment()
    initialize_database(settings.database_path)
    application = create_application()
    window = MainWindow(settings=settings)
    window.show()
    return application.exec()


if __name__ == "__main__":
    raise SystemExit(main())