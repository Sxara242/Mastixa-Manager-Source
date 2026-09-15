# Phase 14C — Windows individual plant UI

Status: implementation checkpoint for roadmap Phase 14.

## Goal

Expose the Phase 14A/14B individual plant model to Windows users without changing the existing aggregate planting workflow.

## Scope

- New Windows page: **Μεμονωμένα Φυτά / Δέντρα** under Καταχωρήσεις · Καλλιέργεια.
- Create and edit plant metadata with required field ownership and optional planting-batch link.
- Optional WGS84 coordinates, label, planting date, variety and notes.
- Current projected status/health is shown in the list.
- Append immutable note/health/status events and show deterministic history.
- Soft-delete records and optionally show/restore deleted plants.
- Field/status/search filters.
- Existing page indices remain unchanged; the page is appended after Crop Program.
- English translation coverage is included for the new Windows surface.

## Important behavior

Individual tracking remains optional. The UI never creates one record per aggregate tree automatically and never recalculates `planting_batches.trees_planted` or `trees_alive`.

Once a plant has event history, status and health changes belong in new events. The metadata editor keeps the original base status/health so an edit cannot silently rewrite projected history.

## Validation

Windows UI tests verify projected status/history rendering, deleted-record visibility, the optional-tracking explanation, and startup navigation integration without moving existing page indices.

## Next slice

Phase 14D should expose the same optional plant/history workflow on Android and add real emulator instrumentation before Phase 14 is considered fully closed.
