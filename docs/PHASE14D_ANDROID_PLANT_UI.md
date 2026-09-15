# Phase 14D — Android individual plant UI

Status: implementation checkpoint for roadmap Phase 14.

## Scope

Android now exposes the shared Phase 14 individual-plant contract through a dedicated native screen. The screen uses `PlantTrackingStore`, so it keeps the Phase 14A/14B rules: optional per-plant tracking, optional planting-batch link, WGS84 coordinate pair validation, immutable note/health/status history, projected current health/status, and soft delete/restore.

The Android UI includes:

- create/edit individual plant records;
- field and optional planting-batch selection;
- label, planting date, variety, WGS84 latitude/longitude and notes;
- initial status/health for records without history;
- append-only note, health and status events;
- event-history display;
- field/status/search filters;
- optional display of soft-deleted records and explicit restore;
- a launcher long-press shortcut to open the screen directly.

The screen never recalculates `planting_batches.trees_planted` or `trees_alive` from individual records.

## Replacement / replanting semantics

The aggregate planting workflow still needs a separate cohort-purpose model before Phase 14 is closed. Approved semantics are:

- **initial / establishment planting**: creates the original occupied planting positions;
- **losses**: plants from a cohort that are no longer alive;
- **replacement / replanting**: a new planting into a previously occupied position;
- **historical total plantings**: initial/new-position plantings plus every replacement planted over time;
- **alive today**: current live plants across original and replacement cohorts;
- **planting positions**: physical intended positions, not historical planting attempts.

Example: 500 initial plants, 472 still alive from that cohort, then 28 replacements planted and alive => 500 positions, 28 replacements, 528 historical plantings, 500 alive today and 28 historical losses.

This checkpoint deliberately does not encode replacement purpose inside `material_type` or notes. A dedicated additive persisted classification will be introduced in the next Phase 14 slice with backup/restore and Windows/Android compatibility tests, so existing backup schema 16 is not changed casually.

## Verification

`PlantTrackingUiTest` exercises the real Activity on Android instrumentation, including projection of event history and the shortcut intent destination. Existing `PlantTrackingTest`, `PlantTrackingStoreTest`, and `LocalBackupTest` remain the lower-level contract/persistence/backup coverage.
