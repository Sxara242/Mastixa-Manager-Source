# Phase 10D — Inventory source provenance and corrected re-import contract

Status: IMPLEMENTED CHECKPOINT.

Phase 10D audits automatic inventory consumption corrections on Windows and Windows-to-Android inventory import provenance after the Phase 10B/10C ledger hardening.

## Windows owning-source correction contract

Automatic inventory consumptions are owned by their source records, not by the inventory page.

Current Windows owners are:

- `farm_activity` for Άρδευση & Λίπανση;
- `plant_protection` for Φυτοπροστασία.

The stable owner key is `source_type + source_id`. `sync_consumption()` updates the existing movement for that owner instead of creating manual correction history. The owning source may therefore correct date, field, item and quantity while preserving one source row. Removing the source consumption removes that source-owned movement.

The Phase 10D Windows regression test explicitly proves an item reassignment correction: stock is restored on the old item, consumed on the new item, the local movement id remains the same, and only one row exists for the source pair.

## Export provenance

Windows portable export includes `inventory_movements` through `SELECT *`, so the existing `source_type` and `source_id` columns travel with the exported movement. No name/date matching is used to invent provenance.

## Android import semantics

Android stores three distinct concepts on imported inventory movements:

- `sourceType + sourceId`: provenance copied from the Windows owning source;
- `windowsId`: the Windows movement id used for import trace/deduplication;
- Android local `id`: local database identity.

`windowsId` is deliberately **not** promoted to portable live-sync identity. Imported/source-owned rows remain immutable from ordinary manual inventory editing.

## Corrected re-import bug found and closed

Before 10D, repeat import deduplication required both the mapped Android item id and `windowsId` to match. This produced two unsafe cases when a Windows movement had been corrected after an earlier Android import:

1. same item + changed quantity/metadata could be silently skipped, leaving stale Android history;
2. changed item + same Windows movement id could be inserted again as a second movement.

Phase 10D changes repeat-import handling to search `windowsId` globally. If the previously imported row is byte-semantically equivalent after relationship mapping, it is an idempotent repeat and is skipped. If the same `windowsId` now describes different movement content, import raises an explicit conflict.

This is intentional: a portable export ZIP is an import/archive contract, not a live synchronization channel. A changed Windows row must therefore never be silently treated as unchanged and must never be duplicated. A future explicit reconciliation/sync workflow may define authoritative replacement semantics using a dedicated portable identity contract.

## Shared cross-client fixture

The canonical fixture is kept byte-identical at:

- `tests/fixtures/phase10_inventory_provenance.json`
- `android/app/src/androidTest/assets/phase10_inventory_provenance.json`

It defines one Windows source-owned movement, an owner correction that moves consumption from one item to another, the Windows movement trace id, and the required Android corrected-reimport policy.

## Regression coverage

Windows `tests/test_inventory_provenance_cross_client.py` verifies:

- fixture identity across clients;
- one source row per `source_type + source_id`;
- owner correction reuses the same Windows local movement id;
- item reassignment restores stock on the old item and consumes stock on the new item;
- source deletion restores the remaining stock.

Android `InventoryProvenanceContractTest` verifies:

- source provenance and `windowsId` survive import;
- an identical repeat package is idempotently skipped;
- a changed package row with the same `windowsId` is an explicit conflict rather than a duplicate or silent stale skip;
- imported/source-owned history is not manually editable.

Hosted CI compiles Android instrumentation coverage; runtime instrumentation remains a device/emulator quality gate.

## Next Phase 10 work

With ledger invariants, receipt/expense atomicity and import provenance hardened, the next coherent batch is the planned broader integrity verification: inventory UI/low-stock reporting, backup/restore and migration compatibility, followed by wider desktop + Android CI and runtime instrumentation at the appropriate gate.
