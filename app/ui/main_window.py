from __future__ import annotations

from PySide6.QtWidgets import QListWidget, QMainWindow, QSplitter, QStackedWidget

from app.config.settings import AppSettings
from app.services.natal_service import NatalService
from app.services.person_service import PersonService
from app.ui.clients_view import ClientsView
from app.ui.natal_view import NatalView


class MainWindow(QMainWindow):
    def __init__(
        self,
        settings: AppSettings,
        person_service: PersonService,
        natal_service: NatalService | None,
        natal_error: str | None = None,
    ) -> None:
        super().__init__()
        self._settings = settings
        self._person_service = person_service
        self._natal_service = natal_service
        self._natal_error = natal_error
        self.setWindowTitle("astroapp")
        self.resize(1200, 760)
        self._build_ui()

    def _build_ui(self) -> None:
        root = QSplitter(self)
        self._navigation = QListWidget(root)
        self._navigation.setObjectName("mainNavigation")
        self._navigation.addItems(["Clients", "Natal Chart"])
        self._navigation.currentRowChanged.connect(self._on_navigation_changed)

        self._pages = QStackedWidget(root)
        self._clients_view = ClientsView(self._person_service)
        self._natal_view = NatalView(
            self._person_service,
            self._natal_service,
            natal_error=self._natal_error,
        )
        self._clients_view.person_saved.connect(self._natal_view.refresh_people)
        self._clients_view.person_selected.connect(self._natal_view.show_person)
        self._pages.addWidget(self._clients_view)
        self._pages.addWidget(self._natal_view)
        root.setStretchFactor(1, 1)
        self.setCentralWidget(root)
        self._navigation.setCurrentRow(0)

    def _on_navigation_changed(self, index: int) -> None:
        if index >= 0:
            self._pages.setCurrentIndex(index)
