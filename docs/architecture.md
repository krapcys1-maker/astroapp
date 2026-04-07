# Architecture Notes

This repository starts with a thin desktop shell and a minimal persistence layer.

## Design constraints

- Keep astrology calculations isolated from UI code.
- Prefer typed modules with explicit inputs and outputs.
- Use services to coordinate storage and engine modules.
- Keep bootstrap code simple enough to evolve without large refactors.

## Initial persistence scope

The first database bootstrap only manages schema metadata. Domain tables and repositories will be added in the next step once the core models are introduced.