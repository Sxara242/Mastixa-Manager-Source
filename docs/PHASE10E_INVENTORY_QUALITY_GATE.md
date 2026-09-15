# Phase 10E — Inventory quality gate

Status: QUALITY-GATE CHECKPOINT. No production schema or user-visible behavior change.

Phase 10E verifies the hardened inventory ledger through the remaining Windows runtime surfaces and records the corresponding Android coverage already present in the project.

## Windows focused runtime coverage

`tests/test_inventory_quality_gate.py` adds three end-to-end integrity checks around the existing production code.

### Low-stock UI and metrics

The Windows `InventoryPage` is populated with representative ledger states and refreshed through the normal page path. The test verifies:

- total item count;
- low-stock count, including exhausted items;
- exhausted count;
- row states `OK`, `Χαμηλό`, and `Εξαντλήθηκε`;
- displayed ledger-derived stock values;
- the `Μόνο χαμηλό / εξαντλημένο` filter.

This closes the gap between ledger-level stock tests and the actual Windows inventory presentation.

### Backup / restore fidelity

A real `Database` and `BackupManager` are exercised with:

- an inventory receipt with a linked `inventory_receipt` expense;
- a `farm_activity` source-owned consumption;
- a consistent SQLite backup;
- post-backup mutations;
- restoration through the production SQLite backup API.

After restore, the test verifies that stock, `source_type + source_id`, movement notes and linked expense amount return to the backed-up state. It then edits the restored receipt and proves that the Phase 10C receipt-expense projection trigger still works, demonstrating that backup/restore preserves both data and the hardened database behavior.

### Legacy inventory migration compatibility

The test creates the pre-hardening Windows inventory tables, inserts real ledger history, and then opens them through the current `InventoryPage` migration path.

It verifies that:

- source/provenance and receipt-financial columns are added in place;
- existing stock remains unchanged;
- Phase 10B integrity triggers are installed;
- Phase 10C receipt-expense projection triggers are installed;
- unit changes after history, manual movement item reassignment, and a delete that would create negative stock are all rejected after migration.

No destructive inventory rebuild is used.

## Android coverage audit

Android already contains dedicated instrumentation coverage for the same quality-gate areas, including:

- `InventoryTest` for CRUD, ledger integrity, import behavior, negative-stock protection and migration-related behavior;
- `InventoryUiTest` for inventory UI behavior;
- `LocalBackupTest` for local backup/restore;
- `LegacySchema` and migration-oriented tests for old database compatibility;
- the Phase 10A signed-ledger fixture and Phase 10D provenance fixture/contract.

Hosted CI compiles the Android instrumentation suite through `assembleChecksAndroidTest`. Execution of instrumentation still requires the project device/emulator runtime quality gate; hosted compile success is not represented as device execution.

## Phase 10 state after this checkpoint

With 10E, the planned inventory hardening sequence has executable coverage for:

1. canonical signed-ledger parity;
2. Windows item/movement/delete invariants;
3. atomic receipt-expense projection;
4. owning-source corrections and cross-client provenance;
5. corrected Windows re-import conflict handling;
6. Windows low-stock UI behavior;
7. backup/restore fidelity;
8. legacy migration compatibility.

The next step after green desktop + Android hosted CI is to treat Phase 10 as hosted-CI complete and run the appropriate Android device/emulator instrumentation gate before declaring runtime closure. No duplicate inventory model, mutable stock source-of-truth, fabricated portable identity, or destructive schema rewrite is introduced by 10E.
