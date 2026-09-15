# Phase 12C — Crop program backup and restore

Status: backup/restore gate for Phase 12 before any crop-program editing UI is exposed.

## Goal

Phase 12C makes the four Phase 12B persistence tables recoverable on both clients before users can create or edit crop-program data through the UI.

Covered tables:

- `crop_programs`
- `crop_program_rules`
- `crop_program_assignments`
- `crop_tasks`

## Windows

Windows backups are SQLite database snapshots created through `BackupManager` and therefore already copy additive tables automatically. Phase 12C adds a focused round-trip test proving that a crop program, its rules, its field/season assignment, and a completed task survive backup and restore.

The restore remains an all-database restore; no Phase 12 table is restored independently from the rest of the profile.

## Android logical backup schema 15

Android logical backup advances from backup schema 14 to **backup schema 15**. This is a backup-format version only; the SQLite `FarmStore` database version remains 14 because Phase 12 storage is still additive/lazy.

Schema 15 appends the four Phase 12 tables after the existing schema-14 tables. Existing schema 2–14 backups remain accepted.

When restoring a schema-14-or-older backup, the Phase 12 tables are restored as empty because those backup formats predate crop programs. This gives true full-profile restore semantics instead of accidentally retaining newer Phase 12 data beside an older backup.

## Validation

Before restore, Android stages the backup into an in-memory database and validates:

- exact table/column shape for the claimed logical backup schema;
- crop-program IDs, names, active flags and numeric fields;
- scheduling rules through the same Phase 12A rule engine;
- assignment season ranges and field/program references;
- generated task identity, dates, categories and statuses;
- program and field relationships for retained historical tasks.

A completed/skipped historical task is **not** required to reference a currently present rule, because template edits may legitimately remove a rule while preserving the user's historical decision.

## Round-trip guarantees

Focused tests prove that:

1. schema-15 snapshot/inspect succeeds with Phase 12 data;
2. program metadata, rules, assignments and completed task status survive restore;
3. an emulated schema-14 backup remains readable and clears newer Phase 12 data on full restore;
4. Windows physical SQLite backup/restore preserves the same logical Phase 12 state.

## Next slice

After this gate is green, Phase 12 can expose the first crop-program management UI. Phase 13 still owns the broader calendar/task experience, overdue presentation, notifications and reminders.
