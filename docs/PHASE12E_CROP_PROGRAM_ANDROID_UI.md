# Phase 12E — Crop Program Android UI

Phase 12E exposes the Phase 12 crop-program model in the Android client after the shared generator, additive persistence and backup/restore gates are already in place.

## Scope

- Add **Πρόγραμμα Καλλιέργειας / Crop Program** to the Android cultivation navigation.
- Create and edit crop-program metadata without pre-seeding agronomic recommendations.
- Add, edit and remove deterministic rules using the same `CropProgram.Rule` model as the Phase 12A engine.
- Support fixed-date rules and interval-window rules.
- Assign a program to an existing field and season year and generate tasks through `CropProgramStore`.
- View generated tasks and change their persisted status between `pending`, `completed` and `skipped`.
- Archive a program while preserving completed/skipped task history according to the Phase 12B contract.

The broader calendar, derived overdue state, reminders and background notifications remain Phase 13 work.

## Date and localization rule

Rule dates are entered numerically as `DD/MM`; no month-name selector is used. This avoids locale-dependent English month names in Greek UI. The engine still persists generated due dates in ISO `YYYY-MM-DD` form.

The page is available in Greek and English. User-entered program names, crop names, descriptions, rule titles and notes are never translated.

## Safety

- Program IDs and rule IDs are generated locally with UUIDs and remain implementation identities, not cross-device sync identities.
- Generation continues to use the Phase 12B transaction contract, so regeneration only replaces pending generated work for the exact assignment.
- Completed and skipped decisions survive regeneration and archive operations.
- The UI refuses assignment when no field or no rule exists.
- No automatic completed farm activity, inventory movement, labor record or financial record is created from a crop task.

## Quality gate

Instrumentation coverage navigates from `MainActivity` into the new Android page, creates a program and fixed-date rule using `DD/MM`, assigns it to a field/year, and verifies the generated persisted task. A second flow verifies the English navigation label. The existing Android runtime workflow is extended to run when this UI, navigation or its test changes.
