# Phase 12B — Crop program storage and regeneration safety

Status: persistence checkpoint for the 16-phase roadmap Phase 12.

## Goal

Phase 12B persists reusable crop programs, their rules, field/season assignments, and the planned tasks produced by the Phase 12A deterministic generator.

This remains a data-layer checkpoint. No user-facing crop-program editor or task calendar is exposed yet.

## Additive local schema

Both Windows and Android use the same logical tables:

- `crop_programs` — reusable template metadata and active/archive state
- `crop_program_rules` — ordered deterministic scheduling rules
- `crop_program_assignments` — program + field + season generation record
- `crop_tasks` — generated planned work keyed by `generation_key`

The storage is created lazily and additively. Android remains on database schema version 14 in this checkpoint; opening an existing profile does not require a destructive migration or database recreation.

## Regeneration contract

Generation first runs the Phase 12A engine completely, before any persisted task is removed.

Inside one transaction:

1. only `pending` tasks for the exact `(program_id, field_id, season_year)` assignment are removed;
2. the new deterministic task set is inserted with conflict-ignore semantics;
3. an existing task with the same `generation_key` and status `completed` or `skipped` is preserved unchanged;
4. the assignment generation timestamp is updated.

Therefore a rule edit can replace future pending work without rewriting user decisions or historical completed/skipped work.

If generation fails (for example, a fixed February 29 rule is applied to a non-leap season), no existing persisted task or assignment is changed.

## Archive/delete semantics

A program is archived rather than physically deleted:

- the program row and rules remain available as historical source metadata;
- its assignments are removed;
- its pending generated tasks are removed;
- completed and skipped tasks remain;
- an archived program cannot generate again unless explicitly saved/reactivated.

This satisfies the Phase 12 rule that template deletion/editing must not erase historical completed work.

## Field/profile isolation

Generation requires an existing field in the current local database.

The crop-program tables live inside the same per-profile database as the field data, so a second profile/database does not see programs, assignments, or tasks from the first one. No cross-device sync identity is inferred.

## Migration rollback proof

The schema creator does not commit internally. Focused Windows and Android tests create the additive schema inside a caller-owned transaction and prove that rolling the transaction back removes the new tables.

## Backup boundary

Phase 12B intentionally does **not** expose UI that can create crop-program data. Android logical backup schema 14 and the Windows user-facing backup/export surface are therefore not yet extended in this checkpoint.

Backup/restore support for the four Phase 12 tables is a required gate **before** crop-program/task editing is exposed to users. This prevents user-created Phase 12 data from existing without a supported backup path.

## Validation targets

Focused tests cover:

- additive migration rollback;
- deterministic persistence of the shared Phase 12A generated task set;
- regeneration after template edits;
- preservation of `completed` and `skipped` decisions;
- removal of obsolete pending tasks;
- archive/history behavior;
- failed-generation atomicity;
- profile/database isolation.

The Android emulator workflow also disables Gradle state caching for this long runtime gate. Phase 12A's previous emulator invocation completed all instrumentation tests successfully, but the GitHub job later hit its 35-minute timeout during post-job cleanup; disabling the cache removes that unnecessary cleanup path.
