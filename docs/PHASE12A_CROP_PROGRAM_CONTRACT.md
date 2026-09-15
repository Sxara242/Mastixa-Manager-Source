# Phase 12A — Crop program generation contract

Status: implementation checkpoint for the new 16-phase roadmap Phase 12.

## Goal

Phase 12 turns a cultivation program into deterministic planned tasks for a field. A program is a reusable set of scheduling rules; it is not a PDF, free-form advice, or a completed farm activity.

This checkpoint deliberately implements the shared generation semantics before adding persistence/UI. It does not hard-code agronomic recommendations. Program content can later come from user-created templates, reviewed built-in templates, imports, or future APIs.

## Boundaries

- `farm_calendar.py` remains a read-only projection of historical records. It is not the task store.
- Phase 12 generates planned work only. It does not create completed irrigation, fertilization, protection, labor, inventory, or money records.
- Phase 13 owns calendar/task UI, overdue state, notifications, and reminder delivery.
- No portable sync identity is inferred or claimed by this phase.

## Rule contract

Every rule has:

- `id`: stable non-empty identifier inside the program
- `title`: user-facing task title
- `category`: one of `irrigation`, `fertilization`, `cultivation`, `plant_protection`, `inspection`, `pruning`, `other`
- `schedule_kind`: `fixed_date` or `interval_window`
- `notes`: optional text copied to generated tasks

### fixed_date

Required fields: `month`, `day`.

The task is generated once in `season_year`. Invalid calendar dates are rejected rather than silently moved to another day.

### interval_window

Required fields: `start_month`, `start_day`, `end_month`, `end_day`, `every_days`.

A task is generated on the start date and then every `every_days` days while the date remains inside the inclusive window. `every_days` must be positive.

If the end month/day is earlier than the start month/day, the end belongs to `season_year + 1`. This supports winter programs that cross New Year without special cases in callers.

## Generated task contract

Generation produces read-only task specifications with:

- `generation_key`
- `program_id`
- `rule_id`
- `field_id`
- `season_year`
- `due_date` (`YYYY-MM-DD`)
- `category`
- `title`
- `notes`
- `status = pending`

`generation_key` is deterministic:

`program_id:field_id:rule_id:due_date`

It is an idempotency key for local generation, not a cross-device sync UUID.

Output order is deterministic: `due_date`, then `rule_id`.

Duplicate rule IDs are rejected. Blank IDs/titles/field/program values, unsupported categories/schedules, invalid dates, and non-positive intervals are rejected.

## Cross-client proof

Windows `app/crop_program.py` and Android `CropProgram.java` implement the same contract. Both consume `shared/fixtures/phase12_crop_program.json` in focused tests. The fixture includes fixed dates, repeating windows, and a window that crosses New Year.

## Next Phase 12 slice

Phase 12B may add additive storage for program definitions, field assignments, and generated tasks, with these safety rules:

1. generation remains idempotent by deterministic source key;
2. regeneration must not overwrite completed/skipped user decisions;
3. deleting or editing a template must not erase historical completed work;
4. field/profile isolation must be explicit;
5. persistence is introduced with migration and rollback tests on both clients before UI integration.
