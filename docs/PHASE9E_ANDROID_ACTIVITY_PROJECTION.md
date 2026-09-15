# Phase 9E — Android activity projection

Status: implementation checkpoint for the Android read-only projection. This step does not add a new event table, migration, Android schema version, or sync identity mapping.

## Scope

`ActivityProjection` reads one profile-local `FarmStore` and one field and projects the existing Android sources into the Phase 9 v1 event contract:

- `production` → `harvest`
- `farm_activities` → `irrigation` / `fertilization`
- `planting_batches` → `planting`
- `plant_protection_records` → `plant_protection`
- `labor_entries` → `cultivation_work`
- `gis_records(kind='point')` with `point_type=note/problem` → `observation`

The query joins the selected active field and excludes source tombstones. Dangling/wrong-field records therefore do not leak into another field timeline.

## Time semantics

Date-only business records accept only valid ISO `YYYY-MM-DD`; invalid values project as `event_date=null`, `event_at=null`, `time_basis=unknown`. No current date/time fallback is used.

GIS observations use `created_at` as the recorded instant. A valid integer epoch-millisecond value produces UTC `event_date`, preserves the exact `event_at`, and uses `time_basis=recorded`.

Ordering matches the contract: known date descending; on the same date exact recorded instants before date-only items, exact instants descending; then lexical source type/id; unknown dates last.

Explicit irrigation/fertilization statuses map to `planned`, `completed`, `cancelled`, or `unknown`. Other sources omit status.

## Identity and isolation

Local identity remains `(scope_id, source_ref.type, source_ref.id, field_id)`. `scope_id` is supplied by the caller and must be non-empty. Android UUIDs remain local source IDs. Phase 9E does not infer Windows identity from `windows_id`, names, KAEK, or dates and does not emit `sync_ref`; shared cross-device identity remains a later Phase 9F concern.

## QA

`ActivityProjectionTest` covers all seven activity kinds from the six source families, deterministic mixed date/timestamp ordering, status mapping, field isolation, exclusion of non-observation GIS point types, invalid-date behavior, source tombstones, deleted parent fields, and invalid scope rejection.

This is an Android instrumentation test because the projection intentionally exercises the real profile-local SQLite schema. Hosted CI compiles Android instrumentation tests via `assembleChecksAndroidTest`; real device/emulator execution is a separate runtime gate.

Schema change: **NO**. Android database version remains **14**. Persistent activity/event duplication: **NO**.
