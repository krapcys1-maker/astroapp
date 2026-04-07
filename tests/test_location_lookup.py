from __future__ import annotations

from pathlib import Path

from app.models.location_match import LocationMatch
from app.services.location_lookup_service import LocationLookupService
from app.storage.db import initialize_database
from app.storage.repositories import LocationMatchRepository


class FakeLocationProvider:
    def __init__(self) -> None:
        self.calls: list[tuple[str, int]] = []

    def search(self, query_text: str, limit: int = 5) -> list[LocationMatch]:
        self.calls.append((query_text, limit))
        return [
            LocationMatch(
                query_text=query_text,
                city="Olesno",
                country="Poland",
                latitude=50.8761,
                longitude=18.4209,
                timezone_name="Europe/Warsaw",
                display_name="Olesno, Opolskie, Poland",
                provider="fake",
                rank=0,
            ),
            LocationMatch(
                query_text=query_text,
                city="Olesno",
                country="Poland",
                latitude=50.2056,
                longitude=20.2056,
                timezone_name="Europe/Warsaw",
                display_name="Olesno alternate, Poland",
                provider="fake",
                rank=1,
            ),
        ]


def test_location_match_repository_replaces_and_reads_by_query(tmp_path: Path) -> None:
    database_path = tmp_path / "locations.sqlite3"
    initialize_database(database_path)
    repository = LocationMatchRepository(database_path)

    repository.replace_for_query(
        "Olesno",
        [
            LocationMatch(
                query_text="Olesno",
                city="Olesno",
                country="Poland",
                latitude=50.8761,
                longitude=18.4209,
                timezone_name="Europe/Warsaw",
                display_name="Olesno, Poland",
                provider="fake",
                rank=0,
            )
        ],
    )

    matches = repository.list_for_query("olesno")

    assert len(matches) == 1
    assert matches[0].city == "Olesno"
    assert matches[0].timezone_name == "Europe/Warsaw"


def test_location_lookup_service_caches_provider_results(tmp_path: Path) -> None:
    database_path = tmp_path / "lookup.sqlite3"
    initialize_database(database_path)
    provider = FakeLocationProvider()
    service = LocationLookupService(database_path, provider=provider)

    first = service.search("Olesno", limit=5)
    second = service.search("Olesno", limit=5)

    assert len(first) == 2
    assert len(second) == 2
    assert provider.calls == [("Olesno", 5)]
    assert second[0].display_name == "Olesno, Opolskie, Poland"


def test_location_lookup_service_falls_back_to_cached_matches(tmp_path: Path) -> None:
    database_path = tmp_path / "lookup_fallback.sqlite3"
    initialize_database(database_path)
    repository = LocationMatchRepository(database_path)
    repository.replace_for_query(
        "Olesno",
        [
            LocationMatch(
                query_text="Olesno",
                city="Olesno",
                country="Poland",
                latitude=50.8761,
                longitude=18.4209,
                timezone_name="Europe/Warsaw",
                display_name="Olesno, Poland",
                provider="fake",
                rank=0,
            )
        ],
    )

    service = LocationLookupService.__new__(LocationLookupService)
    service._repository = repository
    service._provider = None

    matches = service.search("Oles", limit=5)

    assert len(matches) == 1
    assert matches[0].city == "Olesno"
