# Phase 10A — Inventory ledger contract and parity audit

Status: AUDIT / CONTRACT CHECKPOINT. No schema change in 10A.

Phase 10 does **not** start from an empty inventory implementation. Both Windows and Android already have an inventory ledger with items, movements, derived stock, supplier/cost links, automatic consumption links, Windows-to-Android import support, and UI. Phase 10 therefore hardens the existing ledger and closes cross-client integrity gaps instead of introducing a second inventory model.

## Canonical ledger model

Stock is derived from movement history. Neither client should treat a mutable `stock` column as the source of truth.

Canonical movement types and signs are:

- `Παραλαβή` => `+quantity`
- `Κατανάλωση` => `-quantity`
- `Διόρθωση +` => `+quantity`
- `Διόρθωση -` => `-quantity`

`quantity` is always a positive finite magnitude. The movement type owns the sign. Current stock is the signed sum of all active movements for an item.

The ledger must never accept a create, edit, delete, import, or automatic-source update that leaves an item with stock below zero, allowing only the existing floating-point tolerance of `0.000001`.

## Item rules

An inventory item has a stable local identity, name, category, unit, minimum-stock threshold and notes.

The unit is part of the quantity meaning. Once an item has movement history or a linked activity/protection consumption, its unit must not change in place. A different unit requires a different item or an explicit future conversion workflow.

An item with movement history must not be deleted in a way that orphans its ledger.

## Movement rules

A manual movement may change date, type, quantity, field, supplier/cost metadata and notes only while all ledger invariants remain valid. Once a movement exists, its item identity must not be reassigned by an ordinary manual edit.

Imported or automatically generated movements are history/provenance records. They are not edited as ordinary manual movements. Corrections are made through the owning source or by compensating ledger movements according to the source contract.

Receipt cost metadata may create/update a linked expense, but the inventory movement and its financial side effect must be treated as one logical operation. A failure must not leave only one side changed.

## Source provenance

Existing source metadata remains meaningful:

- Windows automatic activity/protection movements use `source_type` + `source_id`.
- Android keeps `sourceType` + `sourceId` and imported Windows traceability in `windowsId`.
- `windowsId` is import/deduplication traceability, not portable sync identity.

Phase 10 does not invent generic live synchronization for inventory. Any future portable inventory identity must use explicit verified sync metadata, following the Phase 9 identity principles rather than matching names, dates or local IDs.

## Existing behavior verified by audit

### Windows

`app/inventory.py` already provides the `Αποθήκη & Εφόδια` UI, item management, four movement types, minimum-stock/zero-stock status, movement history, supplier and cost metadata, linked receipt expenses, year locking, and stock derived from movement sums.

`app/inventory_sync.py` already provides source provenance for automatic consumption and checks available stock before an activity/protection consumption is written.

Manual movement create/update already rejects a projected negative balance.

### Android

`InventoryStore` already uses ledger-derived stock, the same four movement types, positive quantity validation, negative-stock prevention on create/update/delete, item-unit immutability after history/linkage, source/import history protection, pending-change queue writes in the same transaction, and linked receipt money synchronization.

`InventoryImport` validates relationships, deduplicates imported Windows movements by `windowsId`, validates final package balances, and orders positive movements before negative movements during apply so a valid package is not rejected because of an intermediate ordering artifact.

Existing Android instrumentation coverage includes inventory CRUD/integrity, negative-stock rejection, item-unit immutability, import repeatability, rollback, backup/restore, legacy migration and UI coverage. Hosted CI compiles these instrumentation tests; it does not execute them without an emulator/device runtime job.

## Parity gaps found in 10A audit

The following Windows behaviors are weaker than Android and are Phase 10 hardening targets:

1. Windows item editing currently permits changing `unit` even when the item already has movement history.
2. Windows manual movement editing currently permits changing `item_id`; Android keeps movement item identity stable.
3. Windows manual movement deletion does not currently perform the same projected-balance check as Android, so deleting a positive historical movement can make the computed balance negative.
4. Windows movement + linked expense updates are performed through separate committed database calls. This is not yet equivalent to Android's transactional movement/pending-change/money update boundary and needs an atomicity hardening pass.

These are implementation gaps, not reasons to replace the existing schema.

## Cross-client fixture

`tests/fixtures/phase10_inventory_ledger.json` is the canonical signed-ledger fixture. An identical Android instrumentation asset is kept at `android/app/src/androidTest/assets/phase10_inventory_ledger.json`.

The fixture proves that both clients interpret the same movement sequence with the same signs, running balances and final stock. Windows additionally exercises `current_stock()` and `ensure_can_consume()` against the shared fixture. Android exercises the same fixture through `InventoryStore.signed()`; the existing Android inventory tests cover persistence-side negative-stock rejection.

## Phase 10 implementation order after 10A

1. Close the Windows item-unit, movement-item and delete-negative-stock gaps with focused tests.
2. Make the Windows inventory movement + linked expense write path atomic without changing user-visible ledger semantics.
3. Audit import/export and automatic activity/protection corrections against the hardened rules on both clients.
4. Add cross-client fixtures for corrections/import provenance where useful.
5. Verify UI behavior, low-stock reporting, backup/restore and migration compatibility.
6. Run broader desktop + Android CI, followed by Android runtime instrumentation at the appropriate device/emulator quality gate.

No duplicate inventory tables, mutable stock column, fabricated sync identity, or destructive schema rewrite is introduced by this checkpoint.
