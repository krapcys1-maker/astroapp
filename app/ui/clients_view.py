from __future__ import annotations

from PySide6.QtCore import QDate, Qt, QTime, Signal
from PySide6.QtWidgets import (
    QDateEdit,
    QDoubleSpinBox,
    QFormLayout,
    QFrame,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QPushButton,
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
        elif self._clients_list.currentItem() is None:
            self._clients_list.setCurrentRow(0)

    def _build_ui(self) -> None:
        outer_layout = QVBoxLayout(self)
        outer_layout.setContentsMargins(0, 0, 0, 0)
        outer_layout.setSpacing(0)

        centered_layout = QHBoxLayout()
        centered_layout.setContentsMargins(0, 0, 0, 0)
        centered_layout.setSpacing(0)
        centered_layout.addStretch(1)

        page = QWidget(self)
        page.setMaximumWidth(1320)
        layout = QVBoxLayout(page)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(16)

        title = QLabel("Clients")
        title.setObjectName("pageTitle")
        layout.addWidget(title)

        subtitle = QLabel(
            "Create and maintain birth profiles before calculating charts "
            "or running transit windows."
        )
        subtitle.setObjectName("pageSubtitle")
        subtitle.setWordWrap(True)
        layout.addWidget(subtitle)

        body = QHBoxLayout()
        body.setSpacing(16)

        list_card = QFrame(page)
        list_card.setObjectName("sectionCard")
        list_card.setMinimumWidth(280)
        list_card.setMaximumWidth(320)
        list_layout = QVBoxLayout(list_card)
        list_layout.setContentsMargins(18, 18, 18, 18)
        list_layout.setSpacing(12)

        list_heading = QLabel("Client library")
        list_heading.setObjectName("sectionHeading")
        list_layout.addWidget(list_heading)

        list_help = QLabel("Saved profiles stay local in your workspace database.")
        list_help.setObjectName("metaLabel")
        list_help.setWordWrap(True)
        list_layout.addWidget(list_help)

        self._clients_list = QListWidget(list_card)
        self._clients_list.setObjectName("clientsList")
        self._clients_list.currentItemChanged.connect(self._on_person_changed)
        list_layout.addWidget(self._clients_list, 1)

        editor_wrapper = QWidget(page)
        editor_wrapper_layout = QVBoxLayout(editor_wrapper)
        editor_wrapper_layout.setContentsMargins(0, 0, 0, 0)
        editor_wrapper_layout.setSpacing(0)

        editor_card = QFrame(editor_wrapper)
        editor_card.setObjectName("sectionCard")
        editor_card.setMaximumWidth(940)
        editor_layout = QVBoxLayout(editor_card)
        editor_layout.setContentsMargins(22, 22, 22, 22)
        editor_layout.setSpacing(14)

        editor_heading = QLabel("Profile details")
        editor_heading.setObjectName("sectionHeading")
        editor_layout.addWidget(editor_heading)

        editor_help = QLabel(
            "Keep name, notes, coordinates, and timezone together so later "
            "calculations are reproducible."
        )
        editor_help.setObjectName("metaLabel")
        editor_help.setWordWrap(True)
        editor_layout.addWidget(editor_help)

        profile_group = QGroupBox("Profile")
        profile_fields = QFormLayout(profile_group)
        profile_fields.setContentsMargins(16, 18, 16, 16)
        profile_fields.setSpacing(10)

        self._name_input = QLineEdit()
        self._name_input.setPlaceholderText("Client name")
        self._notes_input = QTextEdit()
        self._notes_input.setMinimumHeight(120)
        self._notes_input.setPlaceholderText("Context, reminders, or reading notes")
        profile_fields.addRow("Name", self._name_input)
        profile_fields.addRow("Notes", self._notes_input)

        birth_group = QGroupBox("Birth data")
        birth_fields = QFormLayout(birth_group)
        birth_fields.setContentsMargins(16, 18, 16, 16)
        birth_fields.setSpacing(10)

        self._birth_date_input = QDateEdit()
        self._birth_date_input.setCalendarPopup(True)
        self._birth_date_input.setDate(QDate(1990, 1, 1))
        self._birth_time_input = QTimeEdit()
        self._birth_time_input.setTime(QTime(12, 0))
        self._city_input = QLineEdit()
        self._city_input.setPlaceholderText("City")
        self._country_input = QLineEdit()
        self._country_input.setPlaceholderText("Country")
        self._latitude_input = QDoubleSpinBox()
        self._latitude_input.setDecimals(6)
        self._latitude_input.setRange(-90.0, 90.0)
        self._longitude_input = QDoubleSpinBox()
        self._longitude_input.setDecimals(6)
        self._longitude_input.setRange(-180.0, 180.0)
        self._timezone_input = QLineEdit()
        self._timezone_input.setPlaceholderText("Europe/Warsaw")
        self._timezone_input.setText("UTC")

        birth_fields.addRow("Birth date", self._birth_date_input)
        birth_fields.addRow("Birth time", self._birth_time_input)
        birth_fields.addRow("City", self._city_input)
        birth_fields.addRow("Country", self._country_input)
        birth_fields.addRow("Latitude", self._latitude_input)
        birth_fields.addRow("Longitude", self._longitude_input)
        birth_fields.addRow("Timezone", self._timezone_input)

        actions = QHBoxLayout()
        self._new_button = QPushButton("New client")
        self._new_button.setObjectName("secondaryButton")
        self._new_button.clicked.connect(self._on_new_clicked)
        self._save_button = QPushButton("Save client")
        self._save_button.clicked.connect(self._on_save_clicked)
        actions.addWidget(self._new_button)
        actions.addWidget(self._save_button)

        self._status_label = QLabel("")
        self._status_label.setObjectName("statusBanner")
        self._status_label.setWordWrap(True)

        editor_layout.addWidget(profile_group)
        editor_layout.addWidget(birth_group)
        editor_layout.addLayout(actions)
        editor_layout.addWidget(self._status_label)
        editor_layout.addStretch(1)

        editor_wrapper_layout.addWidget(editor_card)
        editor_wrapper_layout.addStretch(1)

        body.addWidget(list_card)
        body.addWidget(editor_wrapper, 1)
        layout.addLayout(body)

        centered_layout.addWidget(page)
        centered_layout.addStretch(1)
        outer_layout.addLayout(centered_layout)
        outer_layout.addStretch(1)

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
