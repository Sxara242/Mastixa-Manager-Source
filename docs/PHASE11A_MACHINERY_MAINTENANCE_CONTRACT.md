# Phase 11A — Machinery & Maintenance contract audit

Status: BASELINE CONTRACT / PARITY AUDIT.

Phase 11 starts from an already substantial implementation on both Windows and Android. This checkpoint records the behavior that already exists, the cross-client semantics that must remain stable, and the Windows integrity gaps that should be hardened before Phase 11 is closed.

## Existing domain model

Both clients already model two related records:

1. **Equipment** — the durable machine/tool register.
2. **Maintenance / service** — historical service records and future reminders attached to one equipment record.

The common user-facing equipment attributes are:

- name
- category
- brand/model
- equipment code/number
- optional purchase date
- fuel
- meter type (`hours`, `km`, `none`)
- current meter value
- status
- notes

The shared status vocabulary is:

- `Ενεργό`
- `Σε συντήρηση`
- `Εκτός λειτουργίας`
- `Πωλήθηκε`

A maintenance record carries:

- equipment reference
- service date
- service type
- cost
- meter value
- technician/supplier
- notes
- optional next-service date
- optional next-service meter threshold

## Reminder semantics

Windows and Android already use the same practical reminder rules over the most recent reminder-bearing service record for a machine:

- **overdue** when the next service date is before today, or when current meter has reached/passed the next-service meter;
- **upcoming** when the next service date is within 30 days, or the next-service meter is within 50 units;
- otherwise **planned** when a reminder exists;
- otherwise no reminder.

Date and meter conditions are independent: either condition can make a reminder upcoming or overdue.

## Meter semantics

`current_meter` is a high-water mark. Saving a maintenance record with a larger service meter advances the equipment current meter; a smaller historical service value must not lower it.

Android additionally rejects changing an equipment record's meter type after maintenance history exists. This is the desired cross-client integrity rule because changing from hours to kilometres (or vice versa) would reinterpret historical service values.

**Windows gap identified for Phase 11B:** the current Windows equipment edit path does not yet enforce this history lock.

## Maintenance cost projection

A maintenance cost is also represented in Expenses with the source identity:

```text
source_type = equipment_maintenance
source_id   = maintenance record id
```

The maintenance record is the source of truth. The expense is a financial projection of that source record and must remain one-to-one and idempotent across edits.

Expected behavior:

- cost `> 0` => exactly one linked expense;
- editing date/type/cost/technician/notes updates the same logical expense;
- deleting the maintenance record removes the linked expense;
- cost `0` => no linked expense;
- a failed linked-expense write must not leave half of the logical maintenance operation committed.

Android already performs service + expense + meter advancement inside one SQLite transaction.

**Windows gap identified for Phase 11B:** the Windows UI currently performs maintenance insert/update, expense synchronization, maintenance `expense_id` update and equipment meter advancement through separate committed database calls. Successful normal operation is correct, but a forced failure between those writes can leave a partial logical operation.

## Delete and history rules

- Equipment with maintenance history cannot be deleted until its related maintenance records are removed.
- A maintenance record can be edited/deleted only when year-lock policy permits it.
- Android imported Windows equipment/service rows are historical import records and retain their import immutability rules.
- Deleting a maintenance record must not leave an orphan financial projection.

## Import/interoperability boundary

Windows remains the source of the portable ZIP equipment section and Android already has `EquipmentImport` support plus equipment instrumentation tests. Imported Windows IDs are traceability metadata; they are not a claim of live shared synchronization identity.

Phase 11 does not introduce generic machinery cloud sync and does not change the GIS/activity identity contract from Phase 9.

## Phase 11A verification target

The focused Windows baseline test must prove the already-working behavior before hardening:

- equipment creation;
- maintenance creation;
- high-water-mark meter advancement;
- one linked expense per maintenance record;
- expense update without duplication when service is edited;
- upcoming reminder visibility;
- equipment deletion blocked while service history exists;
- service deletion removes the linked expense;
- equipment becomes deletable after its service history is removed.

## Phase 11B hardening target

The next implementation checkpoint should close the two verified Windows gaps without redesigning the domain:

1. prevent meter-type changes once maintenance history exists;
2. make maintenance + expense + meter advancement/removal atomic on Windows, preserving existing UI and export behavior.

No new database version, generic event table, or cross-domain sync system is required for this hardening slice.
