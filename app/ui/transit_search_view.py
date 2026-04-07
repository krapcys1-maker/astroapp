from __future__ import annotations

from PySide6.QtCore import QDate
from PySide6.QtWidgets import (
    QAbstractItemView,
    QComboBox,
    QDateEdit,
    QDoubleSpinBox,
    QFormLayout,
    QFrame,
    QGroupBox,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QPushButton,
    QScrollArea,
    QSizePolicy,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from app.models.aspect_event import AspectEvent
from app.models.transit_query import TransitQuery
from app.services.person_service import PersonService
from app.services.transit_service import TransitService

BODY_OPTIONS = (
    "Sun",
    "Moon",
    "Mercury",
    "Venus",
    "Mars",
    "Jupiter",
    "Saturn",
    "Uranus",
    "Neptune",
    "Pluto",
)
ASPECT_OPTIONS = ("conjunction", "sextile", "square", "trine", "opposition")


class TransitSearchView(QWidget):
    def __init__(
        self,
        person_service: PersonService,
        transit_service: TransitService | None,
        transit_error: str | None = None,
    ) -> None:
        super().__init__()
        self._person_service = person_service
        self._transit_service = transit_service
        self._transit_error = transit_error
        self._events: list[AspectEvent] = []
        self._recent_queries: list[TransitQuery] = []
        self._build_ui()
        self.refresh_people()

    def refresh_people(self) -> None:
        current_person_id = self.current_person_id()
        self._person_selector.blockSignals(True)
        self._person_selector.clear()
        for profile in self._person_service.list_profiles():
            self._person_selector.addItem(profile.person.name, profile.person.id)
        self._person_selector.blockSignals(False)
        if current_person_id is not None:
            self.show_person(current_person_id)
        elif self._person_selector.count() > 0:
            self._person_selector.setCurrentIndex(0)
        self._refresh_recent_queries()

    def show_person(self, person_id: int) -> None:
        for index in range(self._person_selector.count()):
            if self._person_selector.itemData(index) == person_id:
                self._person_selector.setCurrentIndex(index)
                break

    def current_person_id(self) -> int | None:
        person_id = self._person_selector.currentData()
        return None if person_id is None else int(person_id)

    def _build_ui(self) -> None:
        outer_layout = QVBoxLayout(self)
        outer_layout.setContentsMargins(0, 0, 0, 0)
        outer_layout.setSpacing(0)

        scroll_area = QScrollArea(self)
        scroll_area.setWidgetResizable(True)
        scroll_area.setFrameShape(QScrollArea.Shape.NoFrame)
        outer_layout.addWidget(scroll_area)

        scroll_content = QWidget()
        scroll_area.setWidget(scroll_content)

        centered_layout = QHBoxLayout(scroll_content)
        centered_layout.setContentsMargins(0, 0, 0, 0)
        centered_layout.setSpacing(0)
        centered_layout.addStretch(1)

        page = QWidget(self)
        page.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        page.setMaximumWidth(1360)
        layout = QVBoxLayout(page)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(16)

        title = QLabel("Transit Search")
        title.setObjectName("pageTitle")
        layout.addWidget(title)

        subtitle = QLabel(
            "Search date windows where transiting planets aspect a saved "
            "natal chart, then filter and sort the result set."
        )
        subtitle.setObjectName("pageSubtitle")
        subtitle.setWordWrap(True)
        layout.addWidget(subtitle)

        query_card = QFrame(page)
        query_card.setObjectName("sectionCard")
        query_layout = QVBoxLayout(query_card)
        query_layout.setContentsMargins(22, 22, 22, 22)
        query_layout.setSpacing(14)

        query_heading = QLabel("Search setup")
        query_heading.setObjectName("sectionHeading")
        query_layout.addWidget(query_heading)

        form = QFormLayout()
        form.setSpacing(10)
        self._person_selector = QComboBox()
        self._person_selector.currentIndexChanged.connect(self._refresh_recent_queries)
        self._recent_queries_selector = QComboBox()
        self._recent_queries_selector.currentIndexChanged.connect(self._load_selected_recent_query)
        self._start_date_input = QDateEdit()
        self._start_date_input.setCalendarPopup(True)
        self._start_date_input.setDate(QDate.currentDate())
        self._start_date_input.setDisplayFormat("yyyy-MM-dd")
        self._end_date_input = QDateEdit()
        self._end_date_input.setCalendarPopup(True)
        self._end_date_input.setDate(QDate.currentDate().addDays(30))
        self._end_date_input.setDisplayFormat("yyyy-MM-dd")
        self._orb_input = QDoubleSpinBox()
        self._orb_input.setRange(0.1, 15.0)
        self._orb_input.setDecimals(1)
        self._orb_input.setValue(3.0)
        self._filter_input = QLineEdit()
        self._filter_input.setPlaceholderText("Filter results by body or aspect")
        self._filter_input.textChanged.connect(self._apply_filter)

        form.addRow("Person", self._person_selector)
        form.addRow("Recent searches", self._recent_queries_selector)
        form.addRow("Start date", self._start_date_input)
        form.addRow("End date", self._end_date_input)
        form.addRow("Orb", self._orb_input)
        form.addRow("Filter", self._filter_input)
        query_layout.addLayout(form)

        selectors = QHBoxLayout()
        selectors.setSpacing(12)
        self._transit_bodies_list = self._create_multi_select_list(
            "transitBodiesList",
            BODY_OPTIONS,
        )
        self._natal_bodies_list = self._create_multi_select_list(
            "natalBodiesList",
            BODY_OPTIONS,
        )
        self._aspects_list = self._create_multi_select_list(
            "aspectTypesList",
            ASPECT_OPTIONS,
        )
        selectors.addWidget(self._wrap_selector("Transit bodies", self._transit_bodies_list))
        selectors.addWidget(self._wrap_selector("Natal bodies", self._natal_bodies_list))
        selectors.addWidget(self._wrap_selector("Aspects", self._aspects_list))
        query_layout.addLayout(selectors)

        actions = QHBoxLayout()
        self._search_button = QPushButton("Run transit search")
        self._search_button.clicked.connect(self._run_search)
        self._sort_exact_button = QPushButton("Sort by exact time")
        self._sort_exact_button.setObjectName("secondaryButton")
        self._sort_exact_button.clicked.connect(self._sort_by_exact)
        self._clear_button = QPushButton("Reset filters")
        self._clear_button.setObjectName("secondaryButton")
        self._clear_button.clicked.connect(self._reset_form)
        actions.addWidget(self._search_button)
        actions.addWidget(self._sort_exact_button)
        actions.addWidget(self._clear_button)
        query_layout.addLayout(actions)

        self._status_label = QLabel("")
        self._status_label.setObjectName("statusBanner")
        self._status_label.setWordWrap(True)
        query_layout.addWidget(self._status_label)

        layout.addWidget(query_card)

        results_group = QGroupBox("Results")
        results_layout = QVBoxLayout(results_group)
        results_layout.setContentsMargins(16, 18, 16, 16)
        self._results_table = QTableWidget(0, 9)
        self._results_table.setObjectName("transitResultsTable")
        self._results_table.setHorizontalHeaderLabels(
            [
                "Transit body",
                "Natal body",
                "Aspect",
                "Start",
                "Exact",
                "End",
                "Duration",
                "Exact orb",
                "Phase",
            ]
        )
        self._results_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self._results_table.setSelectionMode(QTableWidget.SelectionMode.NoSelection)
        self._results_table.setSortingEnabled(True)
        self._results_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self._results_table.verticalHeader().setVisible(False)
        self._results_table.setMinimumHeight(280)
        results_layout.addWidget(self._results_table)
        layout.addWidget(results_group)
        layout.addStretch(1)

        centered_layout.addWidget(page, 1)
        centered_layout.addStretch(1)
        self._select_all(self._transit_bodies_list)
        self._select_all(self._natal_bodies_list)
        self._select_all(self._aspects_list)
        service_available = self._transit_service is not None
        self._search_button.setEnabled(service_available)
        self._sort_exact_button.setEnabled(service_available)
        if not service_available and self._transit_error:
            self._set_status(self._transit_error)

    @staticmethod
    def _create_multi_select_list(object_name: str, values: tuple[str, ...]) -> QListWidget:
        widget = QListWidget()
        widget.setObjectName(object_name)
        widget.setSelectionMode(QAbstractItemView.SelectionMode.MultiSelection)
        for value in values:
            widget.addItem(QListWidgetItem(value))
        return widget

    @staticmethod
    def _wrap_selector(title: str, widget: QListWidget) -> QGroupBox:
        group = QGroupBox(title)
        layout = QVBoxLayout(group)
        layout.setContentsMargins(12, 18, 12, 12)
        layout.addWidget(widget)
        return group

    @staticmethod
    def _selected_items(widget: QListWidget) -> tuple[str, ...]:
        return tuple(item.text() for item in widget.selectedItems())

    @staticmethod
    def _select_all(widget: QListWidget) -> None:
        for index in range(widget.count()):
            widget.item(index).setSelected(True)

    def _refresh_recent_queries(self, *_args) -> None:
        self._recent_queries_selector.blockSignals(True)
        self._recent_queries_selector.clear()
        self._recent_queries = []
        person_id = self.current_person_id()
        self._recent_queries_selector.addItem("No preset", None)
        if self._transit_service is not None and person_id is not None:
            self._recent_queries = self._transit_service.list_recent_queries(
                person_id=person_id,
                limit=10,
            )
            for query in self._recent_queries:
                self._recent_queries_selector.addItem(self._query_label(query), query.id)
        self._recent_queries_selector.blockSignals(False)
        self._recent_queries_selector.setCurrentIndex(0)

    def _load_selected_recent_query(self, index: int) -> None:
        if index <= 0:
            return
        query = self._recent_queries[index - 1]
        self._start_date_input.setDate(
            QDate(query.start_date.year, query.start_date.month, query.start_date.day)
        )
        self._end_date_input.setDate(
            QDate(query.end_date.year, query.end_date.month, query.end_date.day)
        )
        self._orb_input.setValue(query.orb)
        self._set_selected_values(self._transit_bodies_list, query.selected_transit_bodies)
        self._set_selected_values(self._natal_bodies_list, query.selected_natal_bodies)
        self._set_selected_values(self._aspects_list, query.selected_aspects)
        self._set_status("Loaded recent search preset.")

    def _run_search(self) -> None:
        person_id = self.current_person_id()
        if person_id is None:
            self._set_status("Select a client first.")
            return
        if self._transit_service is None:
            self._set_status(self._transit_error or "Transit service is unavailable.")
            return

        selected_transit_bodies = self._selected_items(self._transit_bodies_list)
        selected_natal_bodies = self._selected_items(self._natal_bodies_list)
        selected_aspects = self._selected_items(self._aspects_list)
        if not selected_transit_bodies or not selected_natal_bodies or not selected_aspects:
            self._set_status("Select at least one transit body, natal body, and aspect.")
            return

        query = TransitQuery(
            person_id=person_id,
            start_date=self._start_date_input.date().toPython(),
            end_date=self._end_date_input.date().toPython(),
            orb=self._orb_input.value(),
            selected_transit_bodies=selected_transit_bodies,
            selected_natal_bodies=selected_natal_bodies,
            selected_aspects=selected_aspects,
        )
        self._events = self._transit_service.search(query)
        self._populate_results(self._events)
        self._refresh_recent_queries()
        self._set_status(f"Found {len(self._events)} transit events.")

    def _sort_by_exact(self) -> None:
        self._events.sort(
            key=lambda event: (
                event.exact_dt is None,
                event.exact_dt or event.start_dt,
            )
        )
        self._apply_filter()

    def _apply_filter(self) -> None:
        filter_text = self._filter_input.text().strip().lower()
        if not filter_text:
            self._populate_results(self._events)
            return
        filtered = [
            event
            for event in self._events
            if filter_text in event.transit_body.lower()
            or filter_text in event.natal_body.lower()
            or filter_text in event.aspect_type.lower()
            or filter_text in event.phase.lower()
        ]
        self._populate_results(filtered)

    def _populate_results(self, events: list[AspectEvent]) -> None:
        self._results_table.setSortingEnabled(False)
        self._results_table.setRowCount(len(events))
        for row_index, event in enumerate(events):
            values = [
                event.transit_body,
                event.natal_body,
                event.aspect_type,
                event.start_dt.isoformat(timespec="minutes"),
                "" if event.exact_dt is None else event.exact_dt.isoformat(timespec="minutes"),
                "" if event.end_dt is None else event.end_dt.isoformat(timespec="minutes"),
                self._format_duration(event),
                "" if event.exact_orb is None else f"{event.exact_orb:.2f}",
                event.phase,
            ]
            for column_index, value in enumerate(values):
                self._results_table.setItem(row_index, column_index, QTableWidgetItem(value))
        self._results_table.setSortingEnabled(True)

    def _reset_form(self) -> None:
        self._start_date_input.setDate(QDate.currentDate())
        self._end_date_input.setDate(QDate.currentDate().addDays(30))
        self._orb_input.setValue(3.0)
        self._filter_input.clear()
        self._select_all(self._transit_bodies_list)
        self._select_all(self._natal_bodies_list)
        self._select_all(self._aspects_list)
        self._recent_queries_selector.setCurrentIndex(0)
        self._set_status("Transit filters reset.")

    @staticmethod
    def _set_selected_values(widget: QListWidget, values: tuple[str, ...]) -> None:
        widget.clearSelection()
        if not values:
            return
        allowed = set(values)
        for index in range(widget.count()):
            item = widget.item(index)
            item.setSelected(item.text() in allowed)

    @staticmethod
    def _format_duration(event: AspectEvent) -> str:
        if event.end_dt is None:
            return "open"
        duration = event.end_dt - event.start_dt
        total_hours = duration.total_seconds() / 3600
        return f"{total_hours:.1f}h"

    @staticmethod
    def _query_label(query: TransitQuery) -> str:
        aspects = ", ".join(query.selected_aspects)
        return (
            f"{query.start_date.isoformat()} to {query.end_date.isoformat()} | "
            f"orb {query.orb:.1f} | {aspects}"
        )

    def _set_status(self, message: str) -> None:
        self._status_label.setText(message)
