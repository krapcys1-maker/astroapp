from __future__ import annotations

from PySide6.QtCore import QDate, Qt, QTime, Signal
from PySide6.QtWidgets import (
    QDateEdit,
    QDoubleSpinBox,
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QPushButton,
    QSplitter,
    QTextEdit,
    QTimeEdit,
    QVBoxLayout,
    QWidget,
)

from app.models.birth_data import BirthData
from app.models.person import Person
from app.models.person_profile import PersonProfile
from app.services.person_service import PersonService


class ClientsView(QWidget):
    person_selected = Signal(int)
    person_saved = Signal(int)

    def __init__(self, person_service: PersonService) -> None:
        super().__init__()
        self._person_service = person_service
        self._current_person_id: int | None = None
        self._build_ui()
        self.refresh_profiles()

    def refresh_profiles(self) -> None:
        profiles = self._person_service.list_profiles()
        current_person_id = self._current_person_id
        self._clients_list.clear()
        for profile in profiles:
            item = QListWidgetItem(profile.person.name)
            item.setData(Qt.ItemDataRole.UserRole, profile.person.id)
            self._clients_list.addItem(item)
            if profile.person.id == current_person_id:
                self._clients_list.setCurrentItem(item)
        if self._clients_list.count() == 0:
            self._set_empty_form()

    def _build_ui(self) -> None:
        layout = QVBoxLayout(self)

        title = QLabel("Clients")
        title.setObjectName("clientsTitle")
        layout.addWidget(title)

        splitter = QSplitter(self)
        self._clients_list = QListWidget(splitter)
        self._clients_list.setObjectName("clientsList")
        self._clients_list.currentItemChanged.connect(self._on_person_changed)

        form_panel = QWidget(splitter)
        form_layout = QVBoxLayout(form_panel)
        fields = QFormLayout()

        self._name_input = QLineEdit()
        self._notes_input = QTextEdit()
        self._birth_date_input = QDateEdit()
        self._birth_date_input.setCalendarPopup(True)
        self._birth_date_input.setDate(QDate(1990, 1, 1))
        self._birth_time_input = QTimeEdit()
        self._birth_time_input.setTime(QTime(12, 0))
        self._city_input = QLineEdit()
        self._country_input = QLineEdit()
        self._latitude_input = QDoubleSpinBox()
        self._latitude_input.setDecimals(6)
        self._latitude_input.setRange(-90.0, 90.0)
        self._longitude_input = QDoubleSpinBox()
        self._longitude_input.setDecimals(6)
        self._longitude_input.setRange(-180.0, 180.0)
        self._timezone_input = QLineEdit()
        self._timezone_input.setText("UTC")

        fields.addRow("Name", self._name_input)
        fields.addRow("Notes", self._notes_input)
        fields.addRow("Birth date", self._birth_date_input)
        fields.addRow("Birth time", self._birth_time_input)
        fields.addRow("City", self._city_input)
        fields.addRow("Country", self._country_input)
        fields.addRow("Latitude", self._latitude_input)
        fields.addRow("Longitude", self._longitude_input)
        fields.addRow("Timezone", self._timezone_input)
        form_layout.addLayout(fields)

        actions = QHBoxLayout()
        self._new_button = QPushButton("New client")
        self._new_button.clicked.connect(self._on_new_clicked)
        self._save_button = QPushButton("Save client")
        self._save_button.clicked.connect(self._on_save_clicked)
        actions.addWidget(self._new_button)
        actions.addWidget(self._save_button)
        form_layout.addLayout(actions)

        self._status_label = QLabel("")
        self._status_label.setObjectName("clientsStatus")
        form_layout.addWidget(self._status_label)
        form_layout.addStretch(1)

        splitter.addWidget(form_panel)
        splitter.setStretchFactor(1, 1)
        layout.addWidget(splitter)

    def _set_empty_form(self) -> None:
        self._current_person_id = None
        self._name_input.clear()
        self._notes_input.clear()
        self._birth_date_input.setDate(QDate(1990, 1, 1))
        self._birth_time_input.setTime(QTime(12, 0))
        self._city_input.clear()
        self._country_input.clear()
        self._latitude_input.setValue(0.0)
        self._longitude_input.setValue(0.0)
        self._timezone_input.setText("UTC")
        self._status_label.setText("Create a client profile to start.")

    def _load_profile(self, profile: PersonProfile) -> None:
        self._current_person_id = profile.person.id
        self._name_input.setText(profile.person.name)
        self._notes_input.setPlainText(profile.person.notes)
        if profile.birth_data is not None:
            self._birth_date_input.setDate(
                QDate(
                    profile.birth_data.birth_date.year,
                    profile.birth_data.birth_date.month,
                    profile.birth_data.birth_date.day,
                )
            )
            self._birth_time_input.setTime(
                QTime(
                    profile.birth_data.birth_time.hour,
                    profile.birth_data.birth_time.minute,
                    profile.birth_data.birth_time.second,
                )
            )
            self._city_input.setText(profile.birth_data.city)
            self._country_input.setText(profile.birth_data.country)
            self._latitude_input.setValue(profile.birth_data.latitude)
            self._longitude_input.setValue(profile.birth_data.longitude)
            self._timezone_input.setText(profile.birth_data.timezone_name)
        self._status_label.setText(f"Loaded client: {profile.person.name}")

    def _on_new_clicked(self) -> None:
        self._clients_list.clearSelection()
        self._set_empty_form()

    def _on_person_changed(
        self,
        current: QListWidgetItem | None,
        previous: QListWidgetItem | None,
    ) -> None:
        del previous
        if current is None:
            return
        person_id = current.data(Qt.ItemDataRole.UserRole)
        if person_id is None:
            return
        profile = self._person_service.get_profile(int(person_id))
        if profile is None:
            return
        self._load_profile(profile)
        self.person_selected.emit(int(person_id))

    def _on_save_clicked(self) -> None:
        person = Person(
            id=self._current_person_id,
            name=self._name_input.text().strip(),
            notes=self._notes_input.toPlainText().strip(),
        )
        birth_data = BirthData(
            person_id=self._current_person_id or 0,
            birth_date=self._birth_date_input.date().toPython(),
            birth_time=self._birth_time_input.time().toPython(),
            city=self._city_input.text().strip(),
            country=self._country_input.text().strip(),
            latitude=self._latitude_input.value(),
            longitude=self._longitude_input.value(),
            timezone_name=self._timezone_input.text().strip() or "UTC",
        )
        profile = self._person_service.save_profile(person, birth_data)
        self._current_person_id = profile.person.id
        self.refresh_profiles()
        self._select_person(profile.person.id)
        self._status_label.setText(f"Saved client: {profile.person.name}")
        if profile.person.id is not None:
            self.person_saved.emit(profile.person.id)

    def _select_person(self, person_id: int | None) -> None:
        if person_id is None:
            return
        for index in range(self._clients_list.count()):
            item = self._clients_list.item(index)
            if item.data(Qt.ItemDataRole.UserRole) == person_id:
                self._clients_list.setCurrentItem(item)
                break
