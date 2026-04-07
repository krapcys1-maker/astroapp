from __future__ import annotations

from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QListWidget,
    QMainWindow,
    QStackedWidget,
    QVBoxLayout,
    QWidget,
)

from app.config.settings import AppSettings
from app.services.location_lookup_service import LocationLookupService
from app.services.natal_service import NatalService
from app.services.person_service import PersonService
from app.services.transit_service import TransitService
from app.ui.clients_view import ClientsView
from app.ui.natal_view import NatalView
from app.ui.transit_search_view import TransitSearchView


class MainWindow(QMainWindow):
    def __init__(
        self,
        settings: AppSettings,
        person_service: PersonService,
        location_service: LocationLookupService | None,
        natal_service: NatalService | None,
        transit_service: TransitService | None,
        location_error: str | None = None,
        natal_error: str | None = None,
        transit_error: str | None = None,
    ) -> None:
        super().__init__()
        self._settings = settings
        self._person_service = person_service
        self._location_service = location_service
        self._natal_service = natal_service
        self._transit_service = transit_service
        self._location_error = location_error
        self._natal_error = natal_error
        self._transit_error = transit_error
        self.setWindowTitle("astroapp")
        self.resize(1200, 760)
        self._build_ui()

    def _build_ui(self) -> None:
        shell = QWidget(self)
        shell.setObjectName("appShell")
        shell_layout = QHBoxLayout(shell)
        shell_layout.setContentsMargins(18, 18, 18, 18)
        shell_layout.setSpacing(18)

        sidebar = QFrame(shell)
        sidebar.setObjectName("sidebarCard")
        sidebar.setFixedWidth(250)
        sidebar_layout = QVBoxLayout(sidebar)
        sidebar_layout.setContentsMargins(18, 18, 18, 18)
        sidebar_layout.setSpacing(16)

        brand_title = QLabel("astroapp")
        brand_title.setObjectName("brandTitle")
        sidebar_layout.addWidget(brand_title)

        brand_subtitle = QLabel("Desktop natal and transit workflow")
        brand_subtitle.setObjectName("brandSubtitle")
        brand_subtitle.setWordWrap(True)
        sidebar_layout.addWidget(brand_subtitle)

        self._navigation = QListWidget(sidebar)
        self._navigation.setObjectName("mainNavigation")
        self._navigation.addItems(["Clients", "Natal Chart", "Transit Search"])
        self._navigation.currentRowChanged.connect(self._on_navigation_changed)
        sidebar_layout.addWidget(self._navigation)

        sidebar_hint = QLabel(
            "Profiles, natal calculations, and transit searches live in one local SQLite workspace."
        )
        sidebar_hint.setObjectName("sidebarHint")
        sidebar_hint.setWordWrap(True)
        sidebar_layout.addWidget(sidebar_hint)
        sidebar_layout.addStretch(1)

        content_card = QFrame(shell)
        content_card.setObjectName("contentCard")
        content_layout = QVBoxLayout(content_card)
        content_layout.setContentsMargins(20, 20, 20, 20)
        content_layout.setSpacing(0)

        self._pages = QStackedWidget(content_card)
        self._clients_view = ClientsView(
            self._person_service,
            location_lookup_service=self._location_service,
            location_error=self._location_error,
        )
        self._natal_view = NatalView(
            self._person_service,
            self._natal_service,
            transit_service=self._transit_service,
            natal_error=self._natal_error,
            transit_error=self._transit_error,
        )
        self._transit_view = TransitSearchView(
            self._person_service,
            self._transit_service,
            transit_error=self._transit_error,
        )
        self._clients_view.person_saved.connect(self._natal_view.refresh_people)
        self._clients_view.person_saved.connect(self._transit_view.refresh_people)
        self._clients_view.person_selected.connect(self._natal_view.show_person)
        self._clients_view.person_selected.connect(self._transit_view.show_person)
        self._pages.addWidget(self._clients_view)
        self._pages.addWidget(self._natal_view)
        self._pages.addWidget(self._transit_view)
        content_layout.addWidget(self._pages)

        shell_layout.addWidget(sidebar)
        shell_layout.addWidget(content_card, 1)
        self.setCentralWidget(shell)
        self.setStyleSheet(_main_window_stylesheet())
        self._navigation.setCurrentRow(0)

    def _on_navigation_changed(self, index: int) -> None:
        if index >= 0:
            self._pages.setCurrentIndex(index)


def _main_window_stylesheet() -> str:
    return """
        QMainWindow, QWidget#appShell {
            background: #f3ede4;
            color: #22302d;
        }
        QFrame#sidebarCard, QFrame#contentCard, QFrame#sectionCard {
            background: #fffdf9;
            border: 1px solid #e4d7c7;
            border-radius: 18px;
        }
        QLabel#brandTitle {
            color: #143f39;
            font-family: Georgia;
            font-size: 24px;
            font-weight: 700;
        }
        QLabel#brandSubtitle {
            color: #566660;
            font-size: 12px;
            line-height: 1.4;
        }
        QLabel#sidebarHint {
            color: #6d7b77;
            font-size: 11px;
            line-height: 1.4;
        }
        QLabel#pageTitle {
            color: #163f39;
            font-family: Georgia;
            font-size: 24px;
            font-weight: 700;
        }
        QLabel#pageSubtitle {
            color: #61706a;
            font-size: 12px;
            line-height: 1.4;
            padding-bottom: 6px;
        }
        QLabel#sectionHeading {
            color: #163f39;
            font-size: 13px;
            font-weight: 600;
        }
        QLabel#statusBanner {
            background: #f6efdf;
            color: #594a2f;
            border: 1px solid #ead9af;
            border-radius: 12px;
            padding: 10px 12px;
        }
        QLabel#metaLabel {
            color: #54615d;
            font-size: 12px;
            padding: 2px 0 4px 0;
        }
        QListWidget#mainNavigation {
            background: transparent;
            border: none;
            outline: none;
            padding: 2px 0;
        }
        QListWidget#mainNavigation::item {
            color: #26413b;
            border-radius: 12px;
            margin: 2px 0;
            padding: 12px 14px;
        }
        QListWidget#mainNavigation::item:selected {
            background: #deeee8;
            color: #143f39;
            font-weight: 600;
        }
        QListWidget#mainNavigation::item:hover:!selected {
            background: #f1f7f4;
        }
        QGroupBox {
            background: #fffdf9;
            border: 1px solid #e6dacb;
            border-radius: 14px;
            margin-top: 12px;
            padding-top: 10px;
            font-weight: 600;
        }
        QGroupBox::title {
            subcontrol-origin: margin;
            left: 12px;
            padding: 0 4px;
            color: #244641;
        }
        QLineEdit,
        QTextEdit,
        QComboBox,
        QDateEdit,
        QTimeEdit,
        QDoubleSpinBox,
        QTableWidget,
        QListWidget {
            background: #fffdfa;
            border: 1px solid #d6cabd;
            border-radius: 10px;
            padding: 6px 8px;
            selection-background-color: #deeee8;
            selection-color: #143f39;
        }
        QTextEdit {
            padding: 8px 10px;
        }
        QTableWidget {
            gridline-color: #ece3d9;
            padding: 0;
        }
        QHeaderView::section {
            background: #f7f0e7;
            color: #43514d;
            border: none;
            border-right: 1px solid #eadfd2;
            border-bottom: 1px solid #eadfd2;
            padding: 8px 10px;
            font-weight: 600;
        }
        QPushButton {
            background: #163f39;
            color: white;
            border: none;
            border-radius: 10px;
            padding: 10px 16px;
            font-weight: 600;
        }
        QPushButton:hover {
            background: #1d4d45;
        }
        QPushButton:pressed {
            background: #0f332d;
        }
        QPushButton:disabled {
            background: #b4b9b7;
            color: #f5f5f5;
        }
        QPushButton#secondaryButton {
            background: #fffdf9;
            color: #163f39;
            border: 1px solid #d6cabd;
        }
        QPushButton#secondaryButton:hover {
            background: #f8f2ea;
        }
        QAbstractSpinBox::up-button,
        QAbstractSpinBox::down-button,
        QComboBox::drop-down {
            border: none;
            background: transparent;
            width: 24px;
        }
    """
