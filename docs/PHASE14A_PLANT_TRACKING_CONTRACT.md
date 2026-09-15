# Phase 14A — Optional individual plant tracking contract

Status: implementation checkpoint for roadmap Phase 14.

## Goal

Phase 14 adds optional individual tree/plant tracking without replacing the existing aggregate planting-batch workflow. Farms that only need counts can keep using `planting_batches`; farms that want per-tree history can opt into individual plant records.

This checkpoint defines shared Windows/Android semantics before persistence or UI is added.

## Boundaries

- Individual plant tracking is optional. No existing field or planting batch is required to create one record per tree.
- `planting_batches.trees_planted` / `trees_alive` remain aggregate source records. Phase 14A does not silently recalculate or overwrite them from individual plants.
- A plant may link to a planting batch, but the link is optional.
- Coordinates are optional and are descriptive data, not identity. A plant ID must never be inferred from row order, label, coordinates, KAEK, or field name.
- This phase records observations; it does not diagnose plant health or provide agronomic recommendations.
- No schema, backup format, sync identity, UI, or notifications change in 14A.

## Plant record

A plant record contains:

- `id`: stable non-empty local identifier
- `field_id`: required owning field
- `planting_batch_id`: optional link to an existing planting batch
- `label`: optional user-facing label/tag
- `planted_date`: optional canonical `YYYY-MM-DD`
- `variety`: optional text
- `latitude` / `longitude`: optional WGS84 pair; both or neither must be supplied
- `status`: `active`, `dead`, or `removed`
- `health`: `unknown`, `good`, `watch`, or `poor`
- `notes`: optional text

Latitude must be in `[-90, 90]` and longitude in `[-180, 180]`.

## Event history

Per-plant events are immutable projection inputs with:

- `id`: unique inside the plant history
- `plant_id`: must match the plant being projected
- `event_date`: canonical `YYYY-MM-DD`
- `kind`: `note`, `health`, or `status`
- `value`: required for `health` and `status`; optional for `note` when notes are present
- `notes`: optional text

Events sort deterministically by `event_date`, then `id`. Duplicate event IDs are rejected. If a plant has a `planted_date`, an event cannot predate it.

No hidden lifecycle transition rule is imposed in 14A. The latest valid status/health event wins. This keeps later correction/import workflows possible without inventing agronomic assumptions.

## Projection

The shared projection returns the plant's current status and health plus:

- stable plant/field/batch metadata
- optional coordinates
- `last_event_date`
- `event_count`

It does not mutate the source record or aggregate planting-batch counts.

## Cross-client proof

Windows `app/plant_tracking.py` and Android `PlantTracking.java` implement the same contract. Both consume `shared/fixtures/phase14_plant_tracking.json` in focused tests.

## Next Phase 14 slice

Phase 14B may add additive persistence for individual plants and plant events. Before UI, it must prove:

1. profile/field isolation;
2. optional planting-batch references do not alter aggregate batch counts automatically;
3. deletion/history behavior is explicit and recoverable;
4. backup/restore coverage exists before user data is exposed in UI;
5. Windows and Android use the same enums, date rules, coordinate rules, and deterministic event ordering.
