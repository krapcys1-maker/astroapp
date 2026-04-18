from __future__ import annotations

from PySide6.QtGui import QGuiApplication
from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QListWidget,
    QMainWindow,
    QSizePolicy,
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
        self.setWindowTitle("AstroLabb")
        self._build_ui()
        self._apply_initial_geometry()

    def _build_ui(self) -> None:
        shell = QWidget(self)
        shell.setObjectName("appShell")
        shell_layout = QHBoxLayout(shell)
        shell_layout.setContentsMargins(14, 14, 14, 14)
        shell_layout.setSpacing(14)

        sidebar = QFrame(shell)
        sidebar.setObjectName("sidebarCard")
        sidebar.setMinimumWidth(220)
        sidebar.setMaximumWidth(280)
        sidebar.setSizePolicy(
            QSizePolicy.Policy.Preferred,
            QSizePolicy.Policy.Expanding,
        )
        sidebar_layout = QVBoxLayout(sidebar)
        sidebar_layout.setContentsMargins(20, 20, 20, 20)
        sidebar_layout.setSpacing(18)

        brand_title = QLabel("AstroLabb")
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
        content_layout.setContentsMargins(24, 24, 24, 24)
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

    def _apply_initial_geometry(self) -> None:
        screen = self.screen() or QGuiApplication.primaryScreen()
        if screen is None:
            self.resize(1280, 800)
            return
        available = screen.availableGeometry()
        width = min(1440, max(720, available.width() - 48))
        height = min(860, max(560, available.height() - 64))
        width = min(width, available.width())
        height = min(height, available.height())
        self.resize(width, height)
        self.move(
            available.x() + max(0, (available.width() - width) // 2),
            available.y() + max(0, (available.height() - height) // 2),
        )


def _main_window_stylesheet() -> str:
    return """
        QMainWindow, QWidget#appShell {
            background: #eef2f7;
            color: #1f2937;
        }
        QFrame#sidebarCard {
            background: #173a3f;
            border: 1px solid #123037;
            border-radius: 24px;
        }
        QFrame#contentCard, QFrame#sectionCard {
            background: #ffffff;
            border: 1px solid #dfe7f1;
            border-radius: 24px;
        }
        QLabel#brandTitle {
            color: #f8fafc;
            font-family: "Trebuchet MS", "Segoe UI", sans-serif;
            font-size: 27px;
            font-weight: 700;
            letter-spacing: 0.6px;
        }
        QLabel#brandSubtitle {
            color: #c9d6db;
            font-size: 12px;
            line-height: 1.4;
        }
        QLabel#sidebarHint {
            color: #b6c6cc;
            font-size: 11px;
            line-height: 1.4;
        }
        QLabel#pageTitle {
            color: #0f172a;
            font-family: "Trebuchet MS", "Segoe UI", sans-serif;
            font-size: 26px;
            font-weight: 700;
            letter-spacing: 0.3px;
        }
        QLabel#pageSubtitle {
            color: #64748b;
            font-size: 12px;
            line-height: 1.4;
            padding-bottom: 6px;
        }
        QLabel#sectionHeading {
            color: #0f172a;
            font-size: 13px;
            font-weight: 600;
        }
        QLabel#statusBanner {
            background: #fff7e8;
            color: #7c5a1c;
            border: 1px solid #f2dfb1;
            border-radius: 12px;
            padding: 10px 12px;
        }
        QLabel#metaLabel {
            color: #667085;
            font-size: 12px;
            padding: 2px 0 4px 0;
        }
        QListWidget#mainNavigation {
            background: transparent;
            border: none;
            outline: none;
            padding: 6px 0;
        }
        QListWidget#mainNavigation::item {
            color: #e6eef1;
            border-radius: 16px;
            margin: 4px 0;
            padding: 14px 16px;
        }
        QListWidget#mainNavigation::item:selected {
            background: #f8fafc;
            color: #173a3f;
            font-weight: 600;
        }
        QListWidget#mainNavigation::item:hover:!selected {
            background: rgba(255, 255, 255, 0.08);
        }
        QGroupBox {
            background: #ffffff;
            border: 1px solid #e8edf4;
            border-radius: 18px;
            margin-top: 12px;
            padding-top: 10px;
            font-weight: 600;
        }
        QGroupBox::title {
            subcontrol-origin: margin;
            left: 12px;
            padding: 0 4px;
            color: #334155;
        }
        QLineEdit,
        QTextEdit,
        QComboBox,
        QDateEdit,
        QTimeEdit,
        QDoubleSpinBox,
        QTableWidget,
        QListWidget {
            background: #ffffff;
            border: 1px solid #dbe3ee;
            border-radius: 12px;
            padding: 6px 8px;
            selection-background-color: #e7f0ee;
            selection-color: #153f3a;
        }
        QListWidget#clientsList,
        QListWidget#locationResultsList,
        QListWidget#transitBodiesList,
        QListWidget#natalBodiesList,
        QListWidget#aspectTypesList {
            background: #fbfdff;
        }
        QLineEdit:focus,
        QTextEdit:focus,
        QComboBox:focus,
        QDateEdit:focus,
        QTimeEdit:focus,
        QDoubleSpinBox:focus {
            border: 1px solid #8cb8ae;
        }
        QTextEdit {
            padding: 8px 10px;
        }
        QTableWidget {
            gridline-color: #edf2f7;
            padding: 0;
        }
        QHeaderView::section {
            background: #f8fafc;
            color: #475569;
            border: none;
            border-right: 1px solid #e6ebf2;
            border-bottom: 1px solid #e6ebf2;
            padding: 8px 10px;
            font-weight: 600;
        }
        QPushButton {
            background: #153f3a;
            color: white;
            border: none;
            border-radius: 12px;
            padding: 10px 16px;
            font-weight: 600;
        }
        QPushButton:hover {
            background: #1d4f49;
        }
        QPushButton:pressed {
            background: #113530;
        }
        QPushButton:disabled {
            background: #c7ced8;
            color: #f8fafc;
        }
        QPushButton#secondaryButton {
            background: #ffffff;
            color: #153f3a;
            border: 1px solid #dbe3ee;
        }
        QPushButton#secondaryButton:hover {
            background: #f7fafc;
        }
        QAbstractSpinBox::up-button,
        QAbstractSpinBox::down-button,
        QComboBox::drop-down {
            border: none;
            background: transparent;
            width: 24px;
        }
    """
