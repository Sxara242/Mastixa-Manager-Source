# Phase 13A — Calendar task state contract

Status: first implementation checkpoint for roadmap Phase 13 (Calendar / Tasks / Notifications).

## Goal

Phase 13 starts from the generated `crop_tasks` created in Phase 12 and defines one shared, deterministic interpretation of task timing for Windows and Android. The stored task lifecycle remains `pending`, `completed`, or `skipped`; overdue and reminder states are derived from `due_date` and the current local date.

## Effective states

For a stored `pending` task:

- `overdue` — due date is before today;
- `due_today` — due date equals today;
- `upcoming` — due date is after today and within the inclusive reminder horizon (default 7 days);
- `pending` — due date is later than the reminder horizon.

Stored `completed` and `skipped` tasks always remain effectively `completed` / `skipped`, even when their due date is in the past or today.

`overdue` is never persisted back into `crop_tasks.status`. This avoids clock-dependent database mutations and keeps Phase 12 regeneration/history semantics intact.

## Reminder severity

Derived in-app reminder severity is:

- `0` for overdue;
- `1` for due today;
- `2` for upcoming;
- no reminder for future pending outside the horizon, completed, or skipped tasks.

This checkpoint defines semantics only. It does not yet claim background/OS notification delivery. Android in-app alert integration and any background reminder delivery are later Phase 13 slices.

## Calendar integration

Windows `Ενιαίο Ημερολόγιο` now includes generated crop-program tasks as a read-only calendar section. Selecting one can open `Πρόγραμμα Καλλιέργειας`; editing task state remains owned by the crop-program page.

The month filter no longer depends on the operating-system Qt locale. Greek month names are explicit, fixing the case where an otherwise Greek UI showed English month names in this filter.

Historical farm records remain read-only projections and are not converted into task rows.

## Cross-client proof

`app/task_calendar.py` and Android `TaskCalendar.java` consume the same `shared/fixtures/phase13_task_calendar.json` fixture. The fixture covers overdue, due-today, inclusive 7-day upcoming, outside-horizon pending, completed-past, and skipped-today cases.

## Next slice

Phase 13B should expose the same task calendar/filtering experience on Android and include derived crop-task reminders in the existing in-app Alerts surface. Background/OS reminder delivery, if added, must remain local/profile-scoped and must not duplicate a second persistent task queue.
