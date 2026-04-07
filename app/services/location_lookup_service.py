from __future__ import annotations

import importlib
from pathlib import Path
from typing import Any

from app.models.location_match import LocationMatch
from app.storage.repositories import LocationMatchRepository


def _load_geopy_modules() -> tuple[Any, Any]:
    try:
        geocoders = importlib.import_module("geopy.geocoders")
        exc_module = importlib.import_module("geopy.exc")
    except ModuleNotFoundError as exc:
        msg = (
            "City lookup requires the optional 'geo' dependencies. "
            "Install them with 'pip install -e .[geo]'."
        )
        raise RuntimeError(msg) from exc
    return geocoders, exc_module


def _load_tzfpy_get_tz() -> Any:
    try:
        tzfpy = importlib.import_module("tzfpy")
    except ModuleNotFoundError as exc:
        msg = (
            "Timezone lookup requires the optional 'geo' dependencies. "
            "Install them with 'pip install -e .[geo]'."
        )
        raise RuntimeError(msg) from exc
    return tzfpy.get_tz


class NominatimLocationProvider:
    def __init__(self) -> None:
        geocoders, exc_module = _load_geopy_modules()
        self._geocoder = geocoders.Nominatim(user_agent="astroapp/0.1")
        self._service_error = exc_module.GeocoderServiceError
        self._timed_out_error = exc_module.GeocoderTimedOut
        self._get_tz = _load_tzfpy_get_tz()

    def search(self, query_text: str, limit: int = 5) -> list[LocationMatch]:
        try:
            matches = self._geocoder.geocode(
                query_text,
                exactly_one=False,
                addressdetails=True,
                limit=limit,
            )
        except (self._service_error, self._timed_out_error) as exc:
            msg = f"City lookup temporarily failed: {exc}"
            raise RuntimeError(msg) from exc
        if not matches:
            return []

        results: list[LocationMatch] = []
        for rank, match in enumerate(matches):
            raw = getattr(match, "raw", {}) or {}
            address = raw.get("address", {})
            city = (
                address.get("city")
                or address.get("town")
                or address.get("village")
                or address.get("municipality")
                or address.get("county")
                or str(match.address).split(",")[0]
            )
            country = address.get("country", "")
            latitude = float(match.latitude)
            longitude = float(match.longitude)
            timezone_name = self._get_tz(longitude, latitude) or "UTC"
            display_name = raw.get("display_name") or str(match.address)
            results.append(
                LocationMatch(
                    query_text=query_text.strip(),
                    city=city,
                    country=country,
                    latitude=latitude,
                    longitude=longitude,
                    timezone_name=timezone_name,
                    display_name=display_name,
                    provider="nominatim",
                    rank=rank,
                )
            )
        return results


class LocationLookupService:
    def __init__(
        self,
        database_path: Path,
        provider: NominatimLocationProvider | None = None,
    ) -> None:
        self._repository = LocationMatchRepository(database_path)
        self._provider = provider or NominatimLocationProvider()

    def search(self, query_text: str, limit: int = 5) -> list[LocationMatch]:
        normalized_query = query_text.strip()
        if not normalized_query:
            return []

        cached = self._repository.list_for_query(normalized_query, limit=limit)
        if cached:
            return cached

        if self._provider is None:
            fallback = self._repository.search_cached(normalized_query, limit=limit)
            if fallback:
                return fallback
            msg = (
                "City lookup is unavailable because the optional 'geo' dependencies "
                "are not installed."
            )
            raise RuntimeError(msg)

        results = self._provider.search(normalized_query, limit=limit)
        if results:
            self._repository.replace_for_query(normalized_query, results)
            return self._repository.list_for_query(normalized_query, limit=limit)
        return self._repository.search_cached(normalized_query, limit=limit)
