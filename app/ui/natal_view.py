from __future__ import annotations

from PySide6.QtWidgets import (
    QComboBox,
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from app.models.chart import Chart
from app.models.chart_settings import NatalChartSettings
from app.services.natal_service import NatalService
from app.services.person_service import PersonService


class NatalView(QWidget):
    def __init__(
        self,
        person_service: PersonService,
        natal_service: NatalService | None,
        natal_error: str | None = None,
    ) -> None:
        super().__init__()
        self._person_service = person_service
        self._natal_service = natal_service
        self._natal_error = natal_error
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
        layout = QVBoxLayout(self)

        title = QLabel("Natal Chart")
        title.setObjectName("natalTitle")
        layout.addWidget(title)

        form = QFormLayout()
        self._person_selector = QComboBox()
        self._person_selector.currentIndexChanged.connect(self._load_saved_chart)
        self._house_system_label = QLabel("Placidus")
        self._zodiac_label = QLabel("tropical")
        form.addRow("Person", self._person_selector)
        form.addRow("House system", self._house_system_label)
        form.addRow("Zodiac", self._zodiac_label)
        layout.addLayout(form)

        actions = QHBoxLayout()
        self._calculate_button = QPushButton("Calculate natal chart")
        self._calculate_button.clicked.connect(self._calculate_chart)
        self._refresh_button = QPushButton("Reload saved chart")
        self._refresh_button.clicked.connect(self._load_saved_chart)
        actions.addWidget(self._calculate_button)
        actions.addWidget(self._refresh_button)
        layout.addLayout(actions)

        self._status_label = QLabel("")
        self._status_label.setObjectName("natalStatus")
        layout.addWidget(self._status_label)

        self._meta_label = QLabel("No chart loaded.")
        self._meta_label.setObjectName("natalMeta")
        layout.addWidget(self._meta_label)

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
        layout.addWidget(QLabel("Planets"))
        layout.addWidget(self._planets_table)
        layout.addWidget(QLabel("Houses"))
        layout.addWidget(self._houses_table)
        layout.addWidget(QLabel("Aspects"))
        layout.addWidget(self._aspects_table)
        layout.addStretch(1)

    @staticmethod
    def _create_table(object_name: str, headers: list[str]) -> QTableWidget:
        table = QTableWidget(0, len(headers))
        table.setObjectName(object_name)
        table.setHorizontalHeaderLabels(headers)
        table.horizontalHeader().setStretchLastSection(True)
        table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        table.setSelectionMode(QTableWidget.SelectionMode.NoSelection)
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

    def _clear_tables(self) -> None:
        self._meta_label.setText("No chart loaded.")
        for table in (self._planets_table, self._houses_table, self._aspects_table):
            table.setRowCount(0)

    def _set_status(self, message: str) -> None:
        self._status_label.setText(message)
