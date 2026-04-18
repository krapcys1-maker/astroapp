from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import QDate, QTime
from PySide6.QtWidgets import (
    QBoxLayout,
    QCheckBox,
    QComboBox,
    QDateEdit,
    QDoubleSpinBox,
    QFileDialog,
    QFormLayout,
    QFrame,
    QGroupBox,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QPushButton,
    QScrollArea,
    QSizePolicy,
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

SIGN_NAMES = [
    "Aries",
    "Taurus",
    "Gemini",
    "Cancer",
    "Leo",
    "Virgo",
    "Libra",
    "Scorpio",
    "Sagittarius",
    "Capricorn",
    "Aquarius",
    "Pisces",
]


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

        scroll_area = QScrollArea(self)
        scroll_area.setWidgetResizable(True)
        scroll_area.setFrameShape(QScrollArea.Shape.NoFrame)
        outer_layout.addWidget(scroll_area)

        scroll_content = QWidget()
        scroll_area.setWidget(scroll_content)

        centered_layout = QHBoxLayout(scroll_content)
        centered_layout.setContentsMargins(0, 0, 0, 0)
        centered_layout.setSpacing(0)

        page = QWidget(self)
        page.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        page.setMaximumWidth(1680)
        layout = QVBoxLayout(page)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(12)
        self._page = page

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

        self._controls_card = QFrame(page)
        self._controls_card.setObjectName("sectionCard")
        controls_layout = QVBoxLayout(self._controls_card)
        controls_layout.setContentsMargins(20, 20, 20, 20)
        controls_layout.setSpacing(10)

        controls_heading = QLabel("Chart setup")
        controls_heading.setObjectName("sectionHeading")
        controls_layout.addWidget(controls_heading)

        form = QFormLayout()
        form.setSpacing(8)
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

        self._debug_overlay_checkbox = QCheckBox("Debug wheel geometry")
        self._debug_overlay_checkbox.toggled.connect(self._chart_debug_toggled)
        controls_layout.addWidget(self._debug_overlay_checkbox)

        transit_group = QGroupBox("Transit overlay")
        transit_layout = QFormLayout(transit_group)
        transit_layout.setContentsMargins(14, 16, 14, 14)
        transit_layout.setSpacing(8)
        self._transit_date_input = QDateEdit()
        self._transit_date_input.setCalendarPopup(True)
        self._transit_date_input.setDate(QDate.currentDate())
        self._transit_date_input.setDisplayFormat("yyyy-MM-dd")
        self._transit_time_input = QTimeEdit()
        self._transit_time_input.setTime(QTime.currentTime())
        self._transit_time_input.setDisplayFormat("HH:mm")
        self._transit_orb_input = QDoubleSpinBox()
        self._transit_orb_input.setRange(0.1, 10.0)
        self._transit_orb_input.setDecimals(1)
        self._transit_orb_input.setValue(3.0)
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
        transit_layout.addRow("Orb", self._transit_orb_input)
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

        chart_group = QGroupBox("Chart wheel")
        chart_layout = QVBoxLayout(chart_group)
        chart_layout.setContentsMargins(16, 18, 16, 16)
        self._chart_widget = NatalChartWidget(chart_group)
        self._chart_widget.setMinimumHeight(680)
        chart_layout.addWidget(self._chart_widget)
        self._top_row = QBoxLayout(QBoxLayout.Direction.LeftToRight)
        self._top_row.setSpacing(16)
        self._controls_card.setMaximumWidth(600)
        self._top_row.addWidget(self._controls_card, 0)
        self._top_row.addWidget(chart_group, 1)
        layout.addLayout(self._top_row)

        self._planets_table = self._create_table(
            "planetsTable",
            ["Body", "Sign", "Degree", "Retrograde", "House"],
        )
        self._houses_table = self._create_table(
            "housesTable",
            ["House", "Sign"],
        )
        self._aspects_table = self._create_table(
            "aspectsTable",
            ["Body A", "Body B", "Aspect", "Orb", "Phase"],
        )

        self._planets_group = QGroupBox("Planets")
        planets_layout = QVBoxLayout(self._planets_group)
        planets_layout.setContentsMargins(16, 18, 16, 16)
        planets_layout.addWidget(self._planets_table)

        self._houses_group = QGroupBox("Houses")
        houses_layout = QVBoxLayout(self._houses_group)
        houses_layout.setContentsMargins(16, 18, 16, 16)
        houses_layout.addWidget(self._houses_table)

        aspects_group = QGroupBox("Aspects")
        aspects_layout = QVBoxLayout(aspects_group)
        aspects_layout.setContentsMargins(16, 18, 16, 16)
        aspects_layout.addWidget(self._aspects_table)

        self._transit_hits_table = self._create_table(
            "transitHitsTable",
            ["Transit body", "Natal body", "Aspect", "Orb", "Phase", "Moment"],
        )
        transit_hits_group = QGroupBox("Transit-to-natal aspects")
        transit_hits_layout = QVBoxLayout(transit_hits_group)
        transit_hits_layout.setContentsMargins(16, 18, 16, 16)
        transit_hits_layout.addWidget(self._transit_hits_table)

        self._tables_top_row = QBoxLayout(QBoxLayout.Direction.LeftToRight)
        self._tables_top_row.setSpacing(16)
        self._planets_group.setMinimumWidth(520)
        self._houses_group.setMaximumWidth(320)
        self._tables_top_row.addWidget(self._planets_group, 1)
        self._tables_top_row.addWidget(self._houses_group, 0)

        self._tables_bottom_row = QBoxLayout(QBoxLayout.Direction.LeftToRight)
        self._tables_bottom_row.setSpacing(16)
        self._tables_bottom_row.addWidget(aspects_group, 1)
        self._tables_bottom_row.addWidget(transit_hits_group, 1)

        layout.addLayout(self._tables_top_row)
        layout.addLayout(self._tables_bottom_row)
        layout.addStretch(1)

        centered_layout.addWidget(page, 1)
        service_available = self._natal_service is not None
        self._calculate_button.setEnabled(service_available)
        self._refresh_button.setEnabled(service_available)
        self._export_button.setEnabled(False)
        self._show_transits_button.setEnabled(self._transit_service is not None)
        self._clear_transits_button.setEnabled(False)
        if not service_available and self._natal_error:
            self._set_status(self._natal_error)
        self._update_responsive_layout()

    def resizeEvent(self, event) -> None:  # type: ignore[override]
        super().resizeEvent(event)
        self._update_responsive_layout()

    def _update_responsive_layout(self) -> None:
        page_width = self._page.width()
        compact_top = page_width < 1260
        compact_tables = page_width < 1380

        self._top_row.setDirection(
            QBoxLayout.Direction.TopToBottom
            if compact_top
            else QBoxLayout.Direction.LeftToRight
        )
        self._tables_top_row.setDirection(
            QBoxLayout.Direction.TopToBottom
            if compact_tables
            else QBoxLayout.Direction.LeftToRight
        )
        self._tables_bottom_row.setDirection(
            QBoxLayout.Direction.TopToBottom
            if compact_tables
            else QBoxLayout.Direction.LeftToRight
        )
        self._controls_card.setMaximumWidth(16777215 if compact_top else 600)
        self._planets_group.setMinimumWidth(0 if compact_tables else 520)
        self._houses_group.setMaximumWidth(16777215 if compact_tables else 320)

    def _chart_debug_toggled(self, checked: bool) -> None:
        self._chart_widget.set_debug_overlay_enabled(checked)

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

    @staticmethod
    def _sign_from_longitude(longitude: float) -> str:
        return SIGN_NAMES[int(longitude // 30) % 12]

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
        hits = self._transit_service.calculate_snapshot_aspects(
            at_dt_utc=transit_dt_utc,
            natal_chart=self._chart_widget.chart,
            orb=self._transit_orb_input.value(),
        )
        self._chart_widget.set_transit_positions(positions)
        self._populate_transit_hits(hits)
        self._clear_transits_button.setEnabled(True)
        self._set_status(
            "Transit overlay updated for "
            f"{self._transit_date_input.date().toString('yyyy-MM-dd')} "
            f"{self._transit_time_input.time().toString('HH:mm')} "
            f"({profile.birth_data.timezone_name})."
        )

    def _clear_transit_overlay(self) -> None:
        self._chart_widget.set_transit_positions([])
        self._transit_hits_table.setRowCount(0)
        self._clear_transits_button.setEnabled(False)
        self._set_status("Transit overlay cleared.")

    def _populate_chart(self, chart: Chart) -> None:
        self._meta_label.setText(
            f"Birth UTC {chart.calculated_at.isoformat()} | "
            f"ASC {chart.ascendant:.2f} | MC {chart.midheaven:.2f}"
            if chart.ascendant is not None and chart.midheaven is not None
            else f"Birth UTC {chart.calculated_at.isoformat()}"
        )

        self._planets_table.setRowCount(len(chart.planet_positions))
        for row_index, position in enumerate(chart.planet_positions):
            values = [
                position.body,
                position.sign,
                f"{position.degree_in_sign:.2f}",
                "yes" if position.retrograde else "no",
                "" if position.house is None else str(position.house),
            ]
            for column_index, value in enumerate(values):
                self._planets_table.setItem(row_index, column_index, QTableWidgetItem(value))

        self._houses_table.setRowCount(len(chart.house_cusps))
        for row_index, house_cusp in enumerate(chart.house_cusps):
            sign_name = self._sign_from_longitude(house_cusp.longitude)
            self._houses_table.setItem(row_index, 0, QTableWidgetItem(str(house_cusp.house_number)))
            self._houses_table.setItem(
                row_index,
                1,
                QTableWidgetItem(sign_name),
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
        self._transit_hits_table.setRowCount(0)
        self._export_button.setEnabled(True)
        self._clear_transits_button.setEnabled(False)

    def _clear_tables(self) -> None:
        self._meta_label.setText("No chart loaded.")
        self._chart_widget.set_chart(None)
        self._chart_widget.set_transit_positions([])
        self._export_button.setEnabled(False)
        self._clear_transits_button.setEnabled(False)
        for table in (
            self._planets_table,
            self._houses_table,
            self._aspects_table,
            self._transit_hits_table,
        ):
            table.setRowCount(0)

    def _set_status(self, message: str) -> None:
        self._status_label.setText(message)

    def _populate_transit_hits(self, hits) -> None:
        self._transit_hits_table.setRowCount(len(hits))
        for row_index, hit in enumerate(hits):
            values = [
                hit.transit_body,
                hit.natal_body,
                hit.aspect_type,
                f"{hit.orb:.2f}",
                hit.phase,
                hit.at_dt.isoformat(timespec="minutes"),
            ]
            for column_index, value in enumerate(values):
                self._transit_hits_table.setItem(row_index, column_index, QTableWidgetItem(value))
