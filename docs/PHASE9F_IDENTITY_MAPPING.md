# Phase 9F — Common activity identity and sync mapping

Status: COMPLETE — verified mapping infrastructure and cross-client identity proof implemented on Windows and Android.

This phase follows the Phase 9 activity contract and the verified Windows/Android projections. It does not create a generic event table and it does not change the existing GIS wire schema.

## Goal

Define the only conditions under which an activity projection may expose a cross-device `sync_ref`:

```text
sync_ref = {
  dataset_id,
  source_uuid,
  field_uuid
}
```

All three values must come from verified synchronization metadata. Local IDs, KAEK, names, dates, descriptions, or import order are never promoted to global identity.

## Identity layers

1. `scope_id` remains local profile/workspace authorization context.
2. `field_id` and `source_ref.id` remain real local database identifiers.
3. `sync_ref` is optional and is present only when a verified common dataset and UUID mapping exists.

The local event key remains:

```text
(scope_id, source_ref.type, source_ref.id, field_id)
```

The portable identity, when available, is:

```text
(dataset_id, source_ref.type, source_uuid, field_uuid)
```

`source_ref.type` remains part of the portable identity so UUIDs from different business domains cannot alias each other accidentally.

## Dataset identity

`dataset_id` must be an explicit stable canonical UUID assigned by synchronization infrastructure. A profile name, database filename, username, device ID, KAEK, or path is not a dataset identity.

A client that has not joined/created a synchronized dataset omits `sync_ref` entirely.

## Field mapping

A field may expose `field_uuid` only when the sync layer has a verified mapping between the local field row and the shared field identity.

Existing verified GIS parcel UUIDs may be reused only where the application already proves that the parcel identity belongs to that field and dataset. A Windows field without such a mapping does not receive a fabricated UUID.

KAEK and field name are attributes, not identity keys.

## Source mapping

Each synchronized activity source row needs a shared `source_uuid` owned by its source synchronization adapter.

Allowed source domains are:

- `production`
- `farm_activity`
- `planting_batch`
- `plant_protection`
- `labor_entry`
- `geo_point`

The projection does not generate UUIDs from integer IDs, `windows_id`, row contents, timestamps, or hashes of business data. Such deterministic derivations can collide after copies/imports and incorrectly merge independent records.

For GIS observations, the already verified GIS record UUID may serve as `source_uuid` when the record belongs to the same synchronized dataset/field mapping.

## Import versus sync

The existing Windows-to-Android imports are additive/import workflows, not proof of shared live identity. An imported `windows_id` is traceability metadata only unless the synchronization layer explicitly records a verified mapping.

Importing the same ZIP twice does not silently create a portable identity claim. Identity is assigned by sync metadata, not inferred from business values.

## Deletion and reassignment

- A deleted/tombstoned source does not appear in the activity projection.
- Reassigning a source to another field changes the local event key and requires the source sync adapter to update the verified field mapping.
- A stale mapping to a missing source does not create a timeline event.
- A mapping conflict is surfaced to the sync/conflict layer; the projection does not choose a winner.

## Implemented mapping storage

Windows and Android now both have an additive activity identity registry with separate verified field and source mappings scoped by local profile and shared dataset. The registry is lazy/additive and does not require adding identity columns to every business table.

The mapping boundary is equivalent to:

```text
field mapping:
(scope_id, dataset_id, local_field_id) -> field_uuid

source mapping:
(scope_id, dataset_id, source_type, local_source_id) -> (source_uuid, local_field_id)
```

Both platforms reject conflicting local/shared mappings rather than inventing a winner. A source mapping can only resolve when its target field mapping is also verified in the same dataset and scope.

## Projection rule

Windows and Android projections continue to produce the Phase 9 v1 contract. They add `sync_ref` only after a verified mapping lookup succeeds for both source and field in the same `dataset_id`.

If any component is missing or inconsistent, `sync_ref` is absent; the local event remains valid.

Windows and Android also preserve the existing verified GIS identity path. Android uses the general registry first and keeps the current GIS `gis_sync_state` path as a verified fallback, so no existing GIS wire v1 behavior had to be rewritten.

## Cross-client proof

Phase 9F includes a shared fixture in which Windows and Android intentionally use different local field/source IDs for the same synchronized production event while sharing the same verified:

- `dataset_id`
- `source_type`
- `source_uuid`
- `field_uuid`

The Windows test and Android instrumentation test both project the same portable `sync_ref`. The Windows test also asserts that the canonical fixture and the Android fixture asset are byte-identical. Scope isolation is verified: the same local row viewed under an unrelated profile does not inherit the portable identity.

This proves that portable identity does not depend on local integer IDs, Android UUID-shaped local IDs, `windows_id`, KAEK, names, dates, or import order.

## Implementation checkpoints completed

1. Current sync metadata audited on both platforms.
2. Additive profile/dataset-scoped mapping registries implemented on Windows and Android.
3. Verified field/source registration and conflict rejection implemented.
4. Windows and Android activity projections integrated with optional verified `sync_ref`.
5. Existing GIS verified identity retained without changing GIS wire v1.
6. Shared cross-client fixture added for a business-domain production activity.
7. Desktop and Android hosted CI are green for the cross-client checkpoint.

## What Phase 9F does not claim

Phase 9F provides the identity/mapping infrastructure needed by future source synchronization adapters. It does **not** claim that generic live synchronization for all business domains already exists.

Today, a business activity receives a portable `sync_ref` only when an explicit trusted adapter or test setup registers its source and field mapping. Existing verified live source synchronization is still the GIS path. Future production/farm-activity/planting/plant-protection/labor sync adapters may populate the general registry without changing the activity projection contract.

## Non-goals preserved

- no generic activity/event persistence table
- no KAEK/name/date based matching
- no UUID derivation from Windows integer IDs
- no `windows_id` promotion to shared identity
- no rewrite of GIS sync schema v1
- no automatic merging of identity conflicts

## Validation note

Hosted GitHub CI executes the desktop test suite and Android unit/build/lint checks, and it compiles Android instrumentation tests via `assembleChecksAndroidTest`. The Android instrumentation tests themselves still require an emulator/device runtime gate; they must not be reported as executed by hosted CI unless a runtime job is added later.

Phase 9F is complete at the identity-contract/infrastructure level. Generic business-domain live synchronization remains intentionally deferred to the phases that introduce or extend those source adapters.
