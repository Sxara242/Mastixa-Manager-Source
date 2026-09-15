# Phase 10C — Atomic inventory receipt / expense projection

Status: IMPLEMENTED CHECKPOINT.

Phase 10C closes the remaining Windows atomicity gap identified in Phase 10A. Inventory receipt movements and their linked expense projection are now protected at the SQLite layer instead of depending on several separately committed `Database.execute()` calls from the UI.

## Contract

The canonical financial link for an inventory receipt is:

- expense `source_type = 'inventory_receipt'`
- expense `source_id = inventory_movements.id`

The movement is the owning record. A receipt with `total_cost > 0` must have the matching source-linked expense; a movement that is no longer a paid receipt must not have that expense.

## Atomic behavior

`ensure_expense_source_schema()` now installs inventory-receipt projection triggers when the inventory ledger exists.

For an inventory movement:

- `INSERT` of a paid `Παραλαβή` creates the source-linked expense in the same SQLite statement.
- `UPDATE` keeps the expense date, description, supplier, partner, amount and notes synchronized in the same SQLite statement.
- changing the movement away from a paid receipt removes the expense in the same SQLite statement.
- `DELETE` removes the expense only after the movement delete itself succeeds.

If an expense projection write fails, SQLite aborts the owning movement write as part of the same statement. There is therefore no committed movement-without-expense partial state from this path.

## Compatibility with the existing UI

`InventoryPage` still calls the existing `sync_expense()` and `delete_expense()` helpers. Their public contract is retained so no page rewrite is required.

For `inventory_receipt` sources:

- `sync_expense()` recognizes a trigger-projected expense and returns its existing id without issuing a redundant second expense update.
- `delete_expense()` does not pre-delete the expense while the owning movement still exists. The movement `AFTER DELETE` trigger performs the deletion only after all ledger guards accept the movement delete.
- the existing `expense_id` backlink update performed by the page remains compatible; portable/canonical provenance remains the explicit expense source pair.

Other expense source types keep their previous helper behavior.

## Regression coverage

`tests/test_inventory_expense_atomicity.py` verifies:

1. forced expense insertion failure rolls back the inventory receipt movement;
2. receipt insert and edit project one stable source-linked expense with matching amount/supplier/notes;
3. the legacy compatibility `sync_expense()` call is idempotent and does not duplicate or rewrite the trigger result;
4. changing receipt semantics removes and can recreate the projection;
5. a Phase 10B negative-stock rejection on movement delete leaves the expense intact even though the UI calls `delete_expense()` first;
6. a successful movement delete removes the linked expense.

## Scope

Phase 10C does not add a mutable stock column, new inventory tables, generic live synchronization, or destructive migrations. It hardens the existing Windows ledger/financial relationship in place.

The next Phase 10 batch can proceed to the planned audit of import/export and automatic activity/protection corrections against the hardened ledger rules, followed by cross-client provenance fixtures where useful.
