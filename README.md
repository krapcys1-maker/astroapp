# astroapp

`astroapp` is an open-source desktop astrology application built with Python and PySide6.

The long-term goal is a practical desktop workflow for natal charts and transit aspect date-range searches. This bootstrap keeps the foundation small, typed, and modular so we can add astrology logic without coupling it to the UI.

## Current bootstrap

- Python 3.12 project configuration via `pyproject.toml`
- PySide6 desktop entry point with a minimal main window
- SQLite bootstrap layer with schema version tracking
- `pytest` and `ruff` configuration
- GitHub Actions workflow for lint and tests
- AGPL-3.0-or-later licensing

## Architecture

The app is organized into focused layers:

- `app/config`: application settings and filesystem paths
- `app/models`: typed domain models
- `app/engine`: astrology calculation backends and calculators
- `app/services`: orchestration layer used by the UI
- `app/storage`: SQLite access and schema bootstrap
- `app/ui`: windows, views, and reusable widgets
- `app/utils`: shared utilities

Business logic should stay out of the UI. The UI should call services, and services should depend on storage and engine modules.

## Roadmap

1. Bootstrap project, tests, CI, and minimal app shell
2. Add typed models plus SQLite repositories
3. Integrate Swiss Ephemeris through a backend abstraction
4. Implement natal chart calculation
5. Build the first end-to-end GUI workflow for clients and natal charts
6. Add transit-to-natal aspect date-range search

## Local development

Create a virtual environment and install the project with dev dependencies:

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -e .[dev]
```

Install the runtime astrology dependency when you are ready to calculate natal charts and transit searches:

```powershell
pip install -e .[astro]
```

For later work on geocoding and timezone lookup, install the separate lookup stack:

```powershell
pip install -e .[geo]
```

On Windows, the `astro` stack is configured around `pysweph`, which ships wheels for the common setups we are targeting. The optional `geo` stack may still require native build tools, depending on the `timezonefinder` wheel availability for your platform.

Run the app:

```powershell
python -m app.main
```

Run tests and linting:

```powershell
pytest
ruff check .
```

Integration tests for the real Swiss Ephemeris backend live in a separate `integration` marker and are intended to run in CI with the optional `astro` dependencies installed.
