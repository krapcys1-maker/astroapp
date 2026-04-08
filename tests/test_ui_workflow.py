from __future__ import annotations

import math
from datetime import UTC, datetime

import pytest
from PySide6.QtCore import QPointF

from app.config.settings import AppSettings
from app.models.aspect import Aspect
from app.models.aspect_event import AspectEvent
from app.models.birth_data import BirthData
from app.models.chart import Chart
from app.models.house_cusp import HouseCusp
from app.models.location_match import LocationMatch
from app.models.planet_position import PlanetPosition
from app.models.transit_aspect_hit import TransitAspectHit
from app.services.person_service import PersonService
from app.storage.db import initialize_database

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


class FakeTransitService:
    def __init__(self) -> None:
        self.queries = []
        self.position_calls = []

    def search(self, query) -> list[AspectEvent]:
        self.queries.append(query)

        return [
            AspectEvent(
                transit_body="Mars",
                natal_body="Sun",
                aspect_type="trine",
                start_dt=datetime(2026, 4, 7, 8, 0, tzinfo=UTC),
                exact_dt=datetime(2026, 4, 7, 12, 0, tzinfo=UTC),
                end_dt=datetime(2026, 4, 7, 18, 0, tzinfo=UTC),
                exact_orb=0.0,
                phase="applying-separating",
            )
        ]

    def list_recent_queries(self, *, person_id: int | None = None, limit: int = 10):
        del limit
        if person_id is None:
            return list(reversed(self.queries))
        return [query for query in reversed(self.queries) if query.person_id == person_id]

    def calculate_positions(self, at_dt_utc, bodies) -> list[PlanetPosition]:
        self.position_calls.append((at_dt_utc, bodies))
        return [
            PlanetPosition("Sun", 15.0, "Aries", 15.0, False, None),
            PlanetPosition("Moon", 82.0, "Gemini", 22.0, False, None),
        ]

    def calculate_snapshot_aspects(self, **kwargs) -> list[TransitAspectHit]:
        at_dt_utc = kwargs["at_dt_utc"]
        return [
            TransitAspectHit(
                transit_body="Sun",
                natal_body="Sun",
                aspect_type="conjunction",
                orb=0.5,
                phase="applying",
                at_dt=at_dt_utc,
            ),
            TransitAspectHit(
                transit_body="Moon",
                natal_body="Moon",
                aspect_type="trine",
                orb=1.2,
                phase="separating",
                at_dt=at_dt_utc,
            ),
        ]


class FakeLocationLookupService:
    def search(self, query_text: str, limit: int = 5) -> list[LocationMatch]:
        del limit
        return [
            LocationMatch(
                query_text=query_text,
                city="Bucharest",
                country="Romania",
                latitude=44.4268,
                longitude=26.1025,
                timezone_name="Europe/Bucharest",
                display_name="Bucharest, Romania",
                provider="fake",
                rank=0,
            )
        ]


def test_main_window_client_and_natal_workflow(tmp_path) -> None:
    from app.main import create_application
    from app.ui.main_window import MainWindow

    application = create_application()
    settings = AppSettings.from_environment()
    database_path = tmp_path / "ui.sqlite3"
    initialize_database(database_path)
    person_service = PersonService(database_path)
    location_service = FakeLocationLookupService()
    natal_service = FakeNatalService()
    transit_service = FakeTransitService()
    window = MainWindow(
        settings=settings,
        person_service=person_service,
        location_service=location_service,
        natal_service=natal_service,
        transit_service=transit_service,
    )
    window.show()
    application.processEvents()

    clients_view = window._clients_view
    clients_view._city_lookup_input.setText("Bucharest")
    clients_view._city_lookup_button.click()
    application.processEvents()

    assert clients_view._location_results_list.count() == 1
    assert clients_view._timezone_input.text() == "Europe/Bucharest"

    clients_view._name_input.setText("Test Client")
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
    assert natal_view._chart_widget.chart is not None
    assert "calculated and saved" in natal_view._status_label.text().lower()

    natal_view._show_transits_button.click()
    application.processEvents()

    assert len(natal_view._chart_widget._transit_positions) == 2
    assert len(transit_service.position_calls) == 1
    assert natal_view._transit_hits_table.rowCount() == 2
    assert "transit overlay updated" in natal_view._status_label.text().lower()

    window._navigation.setCurrentRow(2)
    application.processEvents()

    transit_view = window._transit_view
    transit_items = [
        transit_view._transit_bodies_list.item(index).text()
        for index in range(transit_view._transit_bodies_list.count())
    ]
    natal_items = [
        transit_view._natal_bodies_list.item(index).text()
        for index in range(transit_view._natal_bodies_list.count())
    ]
    assert transit_items[-4:] == ["ASC", "DSC", "IC", "MC"]
    assert natal_items[-4:] == ["ASC", "DSC", "IC", "MC"]
    transit_view._transit_bodies_list.clearSelection()
    transit_view._natal_bodies_list.clearSelection()
    transit_view._aspects_list.clearSelection()
    transit_view._transit_bodies_list.item(4).setSelected(True)
    transit_view._natal_bodies_list.item(0).setSelected(True)
    transit_view._aspects_list.item(3).setSelected(True)
    transit_view._search_button.click()
    application.processEvents()

    assert transit_view._results_table.rowCount() == 1
    assert "found 1 transit events" in transit_view._status_label.text().lower()
    assert transit_view._recent_queries_selector.count() == 2
    assert transit_service.queries[0].selected_transit_bodies == ("Mars",)


def test_natal_chart_widget_exports_png(tmp_path) -> None:
    from app.main import create_application
    from app.ui.widgets import NatalChartWidget

    application = create_application()
    widget = NatalChartWidget()
    widget.resize(640, 640)
    widget.set_chart(
        Chart(
            id=1,
            person_id=1,
            chart_type="natal",
            house_system="Placidus",
            zodiac_type="tropical",
            calculated_at=datetime(2026, 4, 7, 10, 0, tzinfo=UTC),
            ascendant=11.5,
            midheaven=222.0,
            planet_positions=[
                PlanetPosition("Sun", 10.0, "Aries", 10.0, False, 1),
                PlanetPosition("Moon", 13.0, "Aries", 13.0, False, 1),
                PlanetPosition("Mercury", 16.0, "Aries", 16.0, False, 1),
            ],
            house_cusps=[
                HouseCusp(1, 0.0),
                HouseCusp(2, 30.0),
                HouseCusp(3, 60.0),
                HouseCusp(4, 90.0),
                HouseCusp(5, 120.0),
                HouseCusp(6, 150.0),
                HouseCusp(7, 180.0),
                HouseCusp(8, 210.0),
                HouseCusp(9, 240.0),
                HouseCusp(10, 270.0),
                HouseCusp(11, 300.0),
                HouseCusp(12, 330.0),
            ],
            aspects=[
                Aspect("Sun", "Moon", "conjunction", 3.0, "applying"),
                Aspect("Sun", "Mercury", "conjunction", 6.0, "applying"),
            ],
        )
    )
    widget.show()
    application.processEvents()

    export_path = tmp_path / "chart.png"
    assert widget.export_png(export_path) is True
    assert export_path.exists()
    assert export_path.stat().st_size > 0


def test_natal_chart_widget_stacks_close_planets_radially() -> None:
    from app.main import create_application
    from app.ui.widgets import NatalChartWidget
    from app.ui.widgets.chart_geometry import ChartGeometry

    application = create_application()
    widget = NatalChartWidget()
    widget.resize(640, 640)
    chart = Chart(
        id=1,
        person_id=1,
        chart_type="natal",
        house_system="Placidus",
        zodiac_type="tropical",
        calculated_at=datetime(2026, 4, 7, 10, 0, tzinfo=UTC),
        ascendant=11.5,
        midheaven=222.0,
        planet_positions=[
            PlanetPosition("Sun", 10.0, "Aries", 10.0, False, 1),
            PlanetPosition("Moon", 12.0, "Aries", 12.0, False, 1),
            PlanetPosition("Mercury", 14.0, "Aries", 14.0, False, 1),
        ],
        house_cusps=[
            HouseCusp(1, 0.0),
            HouseCusp(2, 30.0),
            HouseCusp(3, 60.0),
            HouseCusp(4, 90.0),
            HouseCusp(5, 120.0),
            HouseCusp(6, 150.0),
            HouseCusp(7, 180.0),
            HouseCusp(8, 210.0),
            HouseCusp(9, 240.0),
            HouseCusp(10, 270.0),
            HouseCusp(11, 300.0),
            HouseCusp(12, 330.0),
        ],
        aspects=[],
    )
    widget.set_chart(chart)
    widget.show()
    application.processEvents()

    geometry = ChartGeometry.from_outer_radius((min(widget.width(), widget.height()) - 60) / 2)
    center_x = widget.width() / 2
    center_y = widget.height() / 2
    layouts = widget._compute_planet_layouts(  # noqa: SLF001
        QPointF(center_x, center_y),
        geometry.planet_ring_radius,
        geometry.planet_band_outer_radius,
        geometry.planet_band_inner_radius,
        chart.ascendant or 0.0,
    )

    assert len(layouts) == 3

    angles = []
    radii = []
    anchor_radii = []
    for layout in layouts:
        dx = layout.glyph_center.x() - center_x
        dy = layout.glyph_center.y() - center_y
        angles.append(math.atan2(-dy, dx))
        radii.append((dx**2 + dy**2) ** 0.5)
        anchor_dx = layout.base_anchor.x() - center_x
        anchor_dy = layout.base_anchor.y() - center_y
        anchor_radii.append((anchor_dx**2 + anchor_dy**2) ** 0.5)

    assert max(angles) - min(angles) < 0.03
    assert radii == sorted(radii, reverse=True)
    available_span = geometry.planet_ring_radius - (geometry.planet_band_inner_radius + 4.0)
    expected_step = min(18.0, available_span / 2)
    assert radii[0] == pytest.approx(geometry.planet_ring_radius)
    assert radii[1] == pytest.approx(geometry.planet_ring_radius - expected_step)
    assert radii[2] == pytest.approx(geometry.planet_ring_radius - (expected_step * 2))
    assert all(
        radius == pytest.approx(geometry.planet_band_outer_radius)
        for radius in anchor_radii
    )


def test_natal_chart_widget_single_planet_stays_on_base_ring() -> None:
    from app.main import create_application
    from app.ui.widgets import NatalChartWidget
    from app.ui.widgets.chart_geometry import ChartGeometry

    application = create_application()
    widget = NatalChartWidget()
    widget.resize(640, 640)
    chart = Chart(
        id=1,
        person_id=1,
        chart_type="natal",
        house_system="Placidus",
        zodiac_type="tropical",
        calculated_at=datetime(2026, 4, 7, 10, 0, tzinfo=UTC),
        ascendant=11.5,
        midheaven=222.0,
        planet_positions=[
            PlanetPosition("Sun", 10.0, "Aries", 10.0, False, 1),
        ],
        house_cusps=[
            HouseCusp(1, 0.0),
            HouseCusp(2, 30.0),
            HouseCusp(3, 60.0),
            HouseCusp(4, 90.0),
            HouseCusp(5, 120.0),
            HouseCusp(6, 150.0),
            HouseCusp(7, 180.0),
            HouseCusp(8, 210.0),
            HouseCusp(9, 240.0),
            HouseCusp(10, 270.0),
            HouseCusp(11, 300.0),
            HouseCusp(12, 330.0),
        ],
        aspects=[],
    )
    widget.set_chart(chart)
    widget.show()
    application.processEvents()

    geometry = ChartGeometry.from_outer_radius((min(widget.width(), widget.height()) - 60) / 2)
    center_x = widget.width() / 2
    center_y = widget.height() / 2
    layouts = widget._compute_planet_layouts(  # noqa: SLF001
        QPointF(center_x, center_y),
        geometry.planet_ring_radius,
        geometry.planet_band_outer_radius,
        geometry.planet_band_inner_radius,
        chart.ascendant or 0.0,
    )

    assert len(layouts) == 1
    dx = layouts[0].glyph_center.x() - center_x
    dy = layouts[0].glyph_center.y() - center_y
    radius = (dx**2 + dy**2) ** 0.5
    assert radius == pytest.approx(geometry.planet_ring_radius)


def test_natal_chart_widget_uses_single_aspect_anchor_radius() -> None:
    from app.main import create_application
    from app.ui.widgets import NatalChartWidget
    from app.ui.widgets.chart_geometry import ChartGeometry

    application = create_application()
    widget = NatalChartWidget()
    widget.resize(640, 640)
    chart = Chart(
        id=1,
        person_id=1,
        chart_type="natal",
        house_system="Placidus",
        zodiac_type="tropical",
        calculated_at=datetime(2026, 4, 7, 10, 0, tzinfo=UTC),
        ascendant=11.5,
        midheaven=222.0,
        planet_positions=[
            PlanetPosition("Sun", 10.0, "Aries", 10.0, False, 1),
            PlanetPosition("Moon", 190.0, "Libra", 10.0, False, 7),
            PlanetPosition("Mercury", 100.0, "Cancer", 10.0, False, 4),
        ],
        house_cusps=[
            HouseCusp(1, 0.0),
            HouseCusp(2, 30.0),
            HouseCusp(3, 60.0),
            HouseCusp(4, 90.0),
            HouseCusp(5, 120.0),
            HouseCusp(6, 150.0),
            HouseCusp(7, 180.0),
            HouseCusp(8, 210.0),
            HouseCusp(9, 240.0),
            HouseCusp(10, 270.0),
            HouseCusp(11, 300.0),
            HouseCusp(12, 330.0),
        ],
        aspects=[],
    )
    widget.set_chart(chart)
    widget.show()
    application.processEvents()

    outer_radius = (min(widget.width(), widget.height()) - 60) / 2
    geometry = ChartGeometry.from_outer_radius(outer_radius)
    center = QPointF(widget.width() / 2, widget.height() / 2)
    anchors = widget._compute_aspect_anchors(  # noqa: SLF001
        center,
        geometry.aspect_radius,
        chart.ascendant or 0.0,
    )

    assert anchors.keys() == {"Sun", "Moon", "Mercury"}

    radii = []
    for point in anchors.values():
        dx = point.x() - center.x()
        dy = point.y() - center.y()
        radii.append((dx**2 + dy**2) ** 0.5)

    assert all(radius == pytest.approx(geometry.aspect_radius) for radius in radii)
