from __future__ import annotations

from datetime import UTC, datetime

import pytest

from app.config.settings import AppSettings
from app.main import create_application
from app.models.aspect import Aspect
from app.models.birth_data import BirthData
from app.models.chart import Chart
from app.models.house_cusp import HouseCusp
from app.models.planet_position import PlanetPosition
from app.services.person_service import PersonService
from app.storage.db import initialize_database
from app.ui.main_window import MainWindow

pytestmark = pytest.mark.ui


class FakeNatalService:
    def __init__(self) -> None:
        self.saved: dict[int, Chart] = {}

    def calculate_and_save_chart(self, *, person_id: int, birth_data: BirthData, settings) -> Chart:
        del birth_data, settings
        chart = Chart(
            id=1,
            person_id=person_id,
            chart_type="natal",
            house_system="Placidus",
            zodiac_type="tropical",
            calculated_at=datetime(2026, 4, 7, 10, 0, tzinfo=UTC),
            ascendant=11.5,
            midheaven=222.0,
            planet_positions=[
                PlanetPosition("Sun", 10.0, "Aries", 10.0, False, 1),
                PlanetPosition("Moon", 70.0, "Gemini", 10.0, False, 3),
            ],
            house_cusps=[
                HouseCusp(1, 0.0),
                HouseCusp(2, 30.0),
            ],
            aspects=[
                Aspect("Sun", "Moon", "sextile", 0.0, "n/a"),
            ],
        )
        self.saved[person_id] = chart
        return chart

    def get_latest_chart(self, person_id: int) -> Chart | None:
        return self.saved.get(person_id)


def test_main_window_client_and_natal_workflow(tmp_path) -> None:
    application = create_application()
    settings = AppSettings.from_environment()
    database_path = tmp_path / "ui.sqlite3"
    initialize_database(database_path)
    person_service = PersonService(database_path)
    natal_service = FakeNatalService()
    window = MainWindow(
        settings=settings,
        person_service=person_service,
        natal_service=natal_service,
    )
    window.show()
    application.processEvents()

    clients_view = window._clients_view
    clients_view._name_input.setText("Test Client")
    clients_view._city_input.setText("Bucharest")
    clients_view._country_input.setText("Romania")
    clients_view._latitude_input.setValue(44.4268)
    clients_view._longitude_input.setValue(26.1025)
    clients_view._timezone_input.setText("UTC")
    clients_view._save_button.click()
    application.processEvents()

    assert clients_view._clients_list.count() == 1

    window._navigation.setCurrentRow(1)
    application.processEvents()

    natal_view = window._natal_view
    natal_view._calculate_button.click()
    application.processEvents()

    assert natal_view._planets_table.rowCount() == 2
    assert natal_view._houses_table.rowCount() == 2
    assert natal_view._aspects_table.rowCount() == 1
    assert "calculated and saved" in natal_view._status_label.text().lower()
