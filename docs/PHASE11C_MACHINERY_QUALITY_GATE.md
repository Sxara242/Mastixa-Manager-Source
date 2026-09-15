# Phase 11C — Machinery & Maintenance quality gate

Status: QUALITY GATE IMPLEMENTED — closure requires exact-head CI success.

This checkpoint closes the remaining Windows user-facing parity gap found after the Phase 11B database hardening. Phase 11 does not redesign the machinery domain; it verifies and hardens the existing equipment, service-history, reminder and expense-projection behavior on Windows and Android.

## Windows integrity after Phase 11B

The database layer now enforces the source-of-truth relationship between maintenance and its financial projection:

- maintenance cost `> 0` has one linked `expenses` row identified by `source_type='equipment_maintenance'` and the maintenance id;
- maintenance insert/update/delete and its linked expense projection happen in the same SQLite statement through triggers;
- a forced expense failure rolls the maintenance statement back instead of leaving a partial logical write;
- deleting the source maintenance record removes its linked expense atomically;
- equipment `current_meter` remains a high-water mark and cannot be reduced by an older/lower service meter;
- changing `meter_type` after maintenance history exists is rejected at database level as defense in depth.

The existing compatibility calls from the Windows UI remain idempotent, so older call paths do not create duplicate linked expenses.

## Phase 11C Windows UI guard

The database trigger deliberately remains the final integrity boundary, but a normal UI edit should not expose a raw SQLite integrity exception to the user.

`EquipmentPage.save_equipment()` therefore checks an attempted meter-type change before issuing the update. When maintenance history exists it:

1. keeps the stored meter type and all other unsaved edits unchanged;
2. keeps the equipment record selected for correction;
3. shows the same practical rule already enforced by Android:

> Η μονάδα μετρητή δεν αλλάζει όταν υπάρχει ιστορικό service.

Changing the meter type before any maintenance history exists remains allowed.

## Cross-client parity

At this checkpoint both clients share the same important business semantics:

- equipment register with `hours`, `km` or `none` meter type;
- maintenance/service history linked to one equipment record;
- current meter as a high-water mark;
- meter-type immutability after service history exists;
- one source-owned expense projection for service cost;
- equipment deletion blocked while service history exists;
- reminder classification based independently on due date and due meter thresholds.

Android already performs service + expense + meter updates transactionally. Windows now protects the equivalent logical relationship at SQLite statement level and provides the matching user-facing meter-type guard.

## Verification

Phase 11 focused Windows coverage now includes:

- baseline equipment/service lifecycle and reminder visibility;
- service edit without duplicate expenses;
- high-water-meter behavior;
- forced expense-write rollback;
- atomic service deletion with its expense;
- database-level meter-type history guard;
- UI-level meter-type guard with a warning instead of an uncaught database error;
- confirmation that a meter-type correction is still allowed before service history exists.

Existing Android equipment instrumentation tests remain the runtime parity suite. Hosted verification runs `assembleChecksAndroidTest`, which compiles those instrumentation tests but does not execute them on an emulator/device. Runtime Android execution remains a separate QA gate and must not be represented as having run merely because hosted verification is green.

## Scope boundary

Phase 11 does not introduce generic machinery cloud synchronization, a generic event table, or new portable identity rules. Imported Windows IDs remain traceability metadata rather than proof of live shared identity. The Phase 9 activity/GIS identity contract remains unchanged.

## Closure rule

Phase 11 is considered complete when the exact branch head containing this quality gate passes both Desktop and Android jobs in `Verify desktop and Android`. A green hosted Android job proves unit/lint/build success and instrumentation-test compilation; it does not replace later emulator/device runtime QA.
