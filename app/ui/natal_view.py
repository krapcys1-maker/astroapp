from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import QDate, QTime
from PySide6.QtWidgets import (
    QComboBox,
    QDateEdit,
    QFileDialog,
    QFormLayout,
    QFrame,
    QGroupBox,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QTimeEdit,
    QVBoxLayout,
    QWidget,
)

from app.models.chart import Chart
from app.models.chart_settings import NatalChartSettings
from app.services.natal_service import NatalService
from app.services.person_service import PersonService
from app.services.transit_service import TransitService
from app.ui.widgets import NatalChartWidget
from app.utils.time_utils import local_datetime_to_utc


class NatalView(QWidget):
    def __init__(
        self,
        person_service: PersonService,
        natal_service: NatalService | None,
        transit_service: TransitService | None = None,
        natal_error: str | None = None,
        transit_error: str | None = None,
    ) -> None:
        super().__init__()
        self._person_service = person_service
        self._natal_service = natal_service
        self._transit_service = transit_service
        self._natal_error = natal_error
        self._transit_error = transit_error
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
            self._load_saved_chart()

    def show_person(self, person_id: int) -> None:
        for index in range(self._person_selector.count()):
            if self._person_selector.itemData(index) == person_id:
                self._person_selector.setCurrentIndex(index)
                self._load_saved_chart()
                break

    def current_person_id(self) -> int | None:
        person_id = self._person_selector.currentData()
        return None if person_id is None else int(person_id)

    def _build_ui(self) -> None:
        outer_layout = QVBoxLayout(self)
        outer_layout.setContentsMargins(0, 0, 0, 0)
        outer_layout.setSpacing(0)

        centered_layout = QHBoxLayout()
        centered_layout.setContentsMargins(0, 0, 0, 0)
        centered_layout.setSpacing(0)
        centered_layout.addStretch(1)

        page = QWidget(self)
        page.setMaximumWidth(1360)
        layout = QVBoxLayout(page)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(16)

        title = QLabel("Natal Chart")
        title.setObjectName("pageTitle")
        layout.addWidget(title)

        subtitle = QLabel(
            "Calculate and reload natal charts from saved birth data, with "
            "the result broken down into planets, houses, and aspects."
        )
        subtitle.setObjectName("pageSubtitle")
        subtitle.setWordWrap(True)
        layout.addWidget(subtitle)

        controls_card = QFrame(page)
        controls_card.setObjectName("sectionCard")
        controls_layout = QVBoxLayout(controls_card)
        controls_layout.setContentsMargins(22, 22, 22, 22)
        controls_layout.setSpacing(14)

        controls_heading = QLabel("Chart setup")
        controls_heading.setObjectName("sectionHeading")
        controls_layout.addWidget(controls_heading)

        form = QFormLayout()
        form.setSpacing(10)
        self._person_selector = QComboBox()
        self._person_selector.currentIndexChanged.connect(self._load_saved_chart)
        self._house_system_label = QLabel("Placidus")
        self._zodiac_label = QLabel("tropical")
        form.addRow("Person", self._person_selector)
        form.addRow("House system", self._house_system_label)
        form.addRow("Zodiac", self._zodiac_label)
        controls_layout.addLayout(form)

        actions = QHBoxLayout()
        self._calculate_button = QPushButton("Calculate natal chart")
        self._calculate_button.clicked.connect(self._calculate_chart)
        self._refresh_button = QPushButton("Reload saved chart")
        self._refresh_button.setObjectName("secondaryButton")
        self._refresh_button.clicked.connect(self._load_saved_chart)
        self._export_button = QPushButton("Export PNG")
        self._export_button.setObjectName("secondaryButton")
        self._export_button.clicked.connect(self._export_chart)
        actions.addWidget(self._calculate_button)
        actions.addWidget(self._refresh_button)
        actions.addWidget(self._export_button)
        controls_layout.addLayout(actions)

        transit_group = QGroupBox("Transit overlay")
        transit_layout = QFormLayout(transit_group)
        transit_layout.setContentsMargins(16, 18, 16, 16)
        transit_layout.setSpacing(10)
        self._transit_date_input = QDateEdit()
        self._transit_date_input.setCalendarPopup(True)
        self._transit_date_input.setDate(QDate.currentDate())
        self._transit_time_input = QTimeEdit()
        self._transit_time_input.setTime(QTime.currentTime())
        self._transit_timezone_label = QLabel("Uses the selected client's timezone")
        transit_actions = QHBoxLayout()
        self._show_transits_button = QPushButton("Show transit overlay")
        self._show_transits_button.setObjectName("secondaryButton")
        self._show_transits_button.clicked.connect(self._show_transit_overlay)
        self._clear_transits_button = QPushButton("Clear overlay")
        self._clear_transits_button.setObjectName("secondaryButton")
        self._clear_transits_button.clicked.connect(self._clear_transit_overlay)
        transit_actions.addWidget(self._show_transits_button)
        transit_actions.addWidget(self._clear_transits_button)
        transit_layout.addRow("Date", self._transit_date_input)
        transit_layout.addRow("Time", self._transit_time_input)
        transit_layout.addRow("Timezone", self._transit_timezone_label)
        transit_layout.addRow("", transit_actions)
        controls_layout.addWidget(transit_group)

        self._status_label = QLabel("")
        self._status_label.setObjectName("statusBanner")
        self._status_label.setWordWrap(True)
        controls_layout.addWidget(self._status_label)

        self._meta_label = QLabel("No chart loaded.")
        self._meta_label.setObjectName("metaLabel")
        self._meta_label.setWordWrap(True)
        controls_layout.addWidget(self._meta_label)

        layout.addWidget(controls_card)

        chart_group = QGroupBox("Chart wheel")
        chart_layout = QVBoxLayout(chart_group)
        chart_layout.setContentsMargins(16, 18, 16, 16)
        self._chart_widget = NatalChartWidget(chart_group)
        chart_layout.addWidget(self._chart_widget)
        layout.addWidget(chart_group)

        self._planets_table = self._create_table(
            "planetsTable",
            ["Body", "Longitude", "Sign", "Degree", "Retrograde", "House"],
        )
        self._houses_table = self._create_table(
            "housesTable",
            ["House", "Longitude"],
        )
        self._aspects_table = self._create_table(
            "aspectsTable",
            ["Body A", "Body B", "Aspect", "Orb", "Phase"],
        )

        planets_group = QGroupBox("Planets")
        planets_layout = QVBoxLayout(planets_group)
        planets_layout.setContentsMargins(16, 18, 16, 16)
        planets_layout.addWidget(self._planets_table)

        houses_group = QGroupBox("Houses")
        houses_layout = QVBoxLayout(houses_group)
        houses_layout.setContentsMargins(16, 18, 16, 16)
        houses_layout.addWidget(self._houses_table)

        aspects_group = QGroupBox("Aspects")
        aspects_layout = QVBoxLayout(aspects_group)
        aspects_layout.setContentsMargins(16, 18, 16, 16)
        aspects_layout.addWidget(self._aspects_table)

        layout.addWidget(planets_group)
        layout.addWidget(houses_group)
        layout.addWidget(aspects_group)
        layout.addStretch(1)

        centered_layout.addWidget(page)
        centered_layout.addStretch(1)
        outer_layout.addLayout(centered_layout)
        outer_layout.addStretch(1)

        service_available = self._natal_service is not None
        self._calculate_button.setEnabled(service_available)
        self._refresh_button.setEnabled(service_available)
        self._export_button.setEnabled(False)
        self._show_transits_button.setEnabled(self._transit_service is not None)
        self._clear_transits_button.setEnabled(False)
        if not service_available and self._natal_error:
            self._set_status(self._natal_error)

    @staticmethod
    def _create_table(object_name: str, headers: list[str]) -> QTableWidget:
        table = QTableWidget(0, len(headers))
        table.setObjectName(object_name)
        table.setHorizontalHeaderLabels(headers)
        table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        table.verticalHeader().setVisible(False)
        table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        table.setSelectionMode(QTableWidget.SelectionMode.NoSelection)
        table.setMinimumHeight(170)
        return table

    def _load_saved_chart(self, *_args) -> None:
        person_id = self.current_person_id()
        if person_id is None or self._natal_service is None:
            self._set_status(self._natal_error or "Natal service is unavailable.")
            self._clear_tables()
            return
        chart = self._natal_service.get_latest_chart(person_id)
        if chart is None:
            self._set_status("No saved natal chart for this client yet.")
            self._clear_tables()
            return
        self._populate_chart(chart)
        self._set_status("Loaded saved natal chart.")

    def _calculate_chart(self) -> None:
        person_id = self.current_person_id()
        if person_id is None:
            self._set_status("Select a client first.")
            return
        if self._natal_service is None:
            self._set_status(self._natal_error or "Natal service is unavailable.")
            return
        profile = self._person_service.get_profile(person_id)
        if profile is None or profile.birth_data is None:
            self._set_status("This client does not have birth data yet.")
            return
        chart = self._natal_service.calculate_and_save_chart(
            person_id=person_id,
            birth_data=profile.birth_data,
            settings=NatalChartSettings(),
        )
        self._populate_chart(chart)
        self._set_status("Natal chart calculated and saved.")

    def _export_chart(self) -> None:
        if self._chart_widget.chart is None:
            self._set_status("Calculate or load a chart before exporting.")
            return
        person_id = self.current_person_id()
        default_name = "natal-chart.png" if person_id is None else f"natal-chart-{person_id}.png"
        selected_path, _selected_filter = QFileDialog.getSaveFileName(
            self,
            "Export natal chart",
            default_name,
            "PNG Image (*.png)",
        )
        if not selected_path:
            return
        self._export_chart_to_path(Path(selected_path))

    def _export_chart_to_path(self, path: Path) -> bool:
        path.parent.mkdir(parents=True, exist_ok=True)
        exported = self._chart_widget.export_png(path)
        if exported:
            self._set_status(f"Exported natal chart to {path.name}.")
        else:
            self._set_status("Natal chart export failed.")
        return exported

    def _show_transit_overlay(self) -> None:
        if self._chart_widget.chart is None:
            self._set_status("Calculate or load a natal chart before showing transits.")
            return
        if self._transit_service is None:
            self._set_status(self._transit_error or "Transit service is unavailable.")
            return
        person_id = self.current_person_id()
        if person_id is None:
            self._set_status("Select a client first.")
            return
        profile = self._person_service.get_profile(person_id)
        if profile is None or profile.birth_data is None:
            self._set_status("This client does not have birth data yet.")
            return
        transit_dt_utc = local_datetime_to_utc(
            self._transit_date_input.date().toPython(),
            self._transit_time_input.time().toPython(),
            profile.birth_data.timezone_name,
        )
        positions = self._transit_service.calculate_positions(
            transit_dt_utc,
            tuple(position.body for position in self._chart_widget.chart.planet_positions),
        )
        self._chart_widget.set_transit_positions(positions)
        self._clear_transits_button.setEnabled(True)
        self._set_status(
            "Transit overlay updated for "
            f"{self._transit_date_input.date().toString('yyyy-MM-dd')} "
            f"{self._transit_time_input.time().toString('HH:mm')} "
            f"({profile.birth_data.timezone_name})."
        )

    def _clear_transit_overlay(self) -> None:
        self._chart_widget.set_transit_positions([])
        self._clear_transits_button.setEnabled(False)
        self._set_status("Transit overlay cleared.")

    def _populate_chart(self, chart: Chart) -> None:
        self._meta_label.setText(
            f"Calculated at {chart.calculated_at.isoformat()} | "
            f"ASC {chart.ascendant:.2f} | MC {chart.midheaven:.2f}"
            if chart.ascendant is not None and chart.midheaven is not None
            else f"Calculated at {chart.calculated_at.isoformat()}"
        )

        self._planets_table.setRowCount(len(chart.planet_positions))
        for row_index, position in enumerate(chart.planet_positions):
            values = [
                position.body,
                f"{position.longitude:.2f}",
                position.sign,
                f"{position.degree_in_sign:.2f}",
                "yes" if position.retrograde else "no",
                "" if position.house is None else str(position.house),
            ]
            for column_index, value in enumerate(values):
                self._planets_table.setItem(row_index, column_index, QTableWidgetItem(value))

        self._houses_table.setRowCount(len(chart.house_cusps))
        for row_index, house_cusp in enumerate(chart.house_cusps):
            self._houses_table.setItem(row_index, 0, QTableWidgetItem(str(house_cusp.house_number)))
            self._houses_table.setItem(
                row_index,
                1,
                QTableWidgetItem(f"{house_cusp.longitude:.2f}"),
            )

        self._aspects_table.setRowCount(len(chart.aspects))
        for row_index, aspect in enumerate(chart.aspects):
            values = [
                aspect.body_a,
                aspect.body_b,
                aspect.aspect_type,
                f"{aspect.orb:.2f}",
                aspect.phase,
            ]
            for column_index, value in enumerate(values):
                self._aspects_table.setItem(row_index, column_index, QTableWidgetItem(value))
        self._chart_widget.set_chart(chart)
        self._chart_widget.set_transit_positions([])
        self._export_button.setEnabled(True)
        self._clear_transits_button.setEnabled(False)

    def _clear_tables(self) -> None:
        self._meta_label.setText("No chart loaded.")
        self._chart_widget.set_chart(None)
        self._chart_widget.set_transit_positions([])
        self._export_button.setEnabled(False)
        self._clear_transits_button.setEnabled(False)
        for table in (self._planets_table, self._houses_table, self._aspects_table):
            table.setRowCount(0)

    def _set_status(self, message: str) -> None:
        self._status_label.setText(message)
