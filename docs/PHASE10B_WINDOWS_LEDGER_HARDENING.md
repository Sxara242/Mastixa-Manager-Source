# Phase 10B — Windows inventory ledger invariant hardening

Status: IMPLEMENTED / REGRESSION-COVERED.

Phase 10B closes the first three Windows parity gaps identified by the Phase 10A audit without changing the inventory schema or user-visible stock model.

## Guards added

The Windows inventory schema helper now installs database-level integrity guards whenever the inventory source schema is ensured:

1. **Item unit immutability after history** — an inventory item's `unit` cannot change once any ledger movement exists for that item.
2. **Manual movement item identity stability** — an existing manual movement cannot be reassigned to a different `item_id`.
3. **Delete-time non-negative stock** — deleting a movement is rejected if the resulting ledger balance for its item would be below `-0.000001`.

These guards sit below the UI so alternate Windows callers cannot bypass the ledger invariants.

## Automatic source corrections

Automatic activity/protection movements remain owned by their source record. The manual movement identity trigger deliberately applies only when `source_type` is empty, so `sync_consumption()` may still move an automatic consumption to another inventory item when the owning activity/protection record is corrected and the destination item has sufficient stock.

Deleting an automatic consumption remains safe because removing a negative movement increases stock. The generic delete guard applies to every movement and therefore also prevents any future source path from deleting a positive movement if that would make stock negative.

## Regression coverage

`tests/test_inventory_ledger_contract.py` now verifies:

- shared Windows/Android signed-ledger fixture parity;
- consumption checks against derived ledger balance;
- unit changes are rejected after item history exists;
- manual movement `item_id` reassignment is rejected;
- automatic source-owned reassignment remains allowed;
- deleting a positive movement is rejected when projected stock would be negative;
- deleting a movement remains allowed when projected stock stays non-negative.

## Remaining Phase 10 work

The next planned batch is the fourth gap from Phase 10A: make the Windows inventory movement + linked expense write path atomic without changing ledger semantics. After that, audit import/export and automatic-source correction behavior against the hardened invariants, then continue with broader parity/UI/backup/migration verification.
