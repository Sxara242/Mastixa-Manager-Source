# Phase 14B — Individual plant persistence and backup

Status: implementation checkpoint for roadmap Phase 14.

## Goal

Persist the optional per-plant model from Phase 14A on Windows and Android before any user-facing plant UI is enabled. Plant events remain append-only projection inputs and aggregate planting-batch counts remain independent.

## Storage

Both clients add two local tables:

- `individual_plants`: stable plant identity, owning field, optional planting-batch link, descriptive metadata, optional WGS84 coordinates, baseline status/health, timestamps, and soft-delete timestamp.
- `plant_events`: immutable event identity, owning plant, canonical event date, `note` / `health` / `status`, value, notes, and creation timestamp.

The tables are additive and do not change the existing field or planting-batch schemas.

## Relationship rules

- The owning field must exist in the current local database/profile.
- An optional planting-batch ID must exist and belong to the same field.
- Saving or deleting an individual plant never changes `planting_batches.trees_planted` or `trees_alive`.
- A plant event must reference an existing, non-deleted plant when appended.
- Existing immutable events are revalidated before plant metadata is edited, so changing `planted_date` cannot make recorded history invalid.

Android profile isolation follows the existing one-database-per-profile model: a plant cannot reference a field from another profile database.

## Deletion and recovery

Plant deletion is soft deletion. The plant row and all events remain stored. A deleted plant can be explicitly restored; no event is deleted or rewritten as part of that operation.

There is deliberately no event edit/delete API in this checkpoint. Corrections can be represented by later events, consistent with the Phase 14A projection contract.

## Backup / restore

### Windows

Windows backups are SQLite snapshots, so the additive `individual_plants` and `plant_events` tables are included automatically. A focused test proves that backup/restore returns both the plant registry and event history.

### Android

The logical Android backup format advances from schema 15 to schema 16 and appends the two Phase 14 tables. Restore validation checks:

- plant enum/date/coordinate rules;
- field ownership;
- optional planting-batch existence and same-field ownership;
- event ownership and complete projected-history validity.

Schema 15 backups remain accepted. Restoring a schema 15 backup intentionally produces an empty per-plant registry because those tables did not exist in that format. Schema 14 compatibility remains intact as well.

## Cross-client semantics

Persistence uses the same Phase 14A enums, canonical dates, coordinate ranges, stable IDs, and deterministic event ordering on Windows and Android. Coordinates remain descriptive data and never become identity.

## Next Phase 14 slice

Phase 14C may expose optional Windows and Android plant-management UI. It should keep the feature opt-in, avoid forcing per-tree entry for farms that only use aggregate planting batches, and provide clear access to plant history without changing aggregate counts automatically.
