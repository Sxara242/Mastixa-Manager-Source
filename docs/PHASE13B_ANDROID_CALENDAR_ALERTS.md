# Phase 13B — Android unified calendar and crop-task alerts

Status: Android UI/reminder checkpoint for roadmap Phase 13.

## Goal

Phase 13B exposes the Phase 13 task timing semantics in the Android UI without creating a second task or notification store. The existing Phase 12 `crop_tasks` rows remain the source of truth, while overdue/today/upcoming are derived at read time through `TaskCalendar`.

## Android unified calendar

Android now has an `Ενιαίο Ημερολόγιο` / `Unified Calendar` read-only surface. It combines:

- production records;
- irrigation/fertilization activities;
- plant-protection records;
- labor records;
- planting records;
- generated crop-program tasks.

The calendar supports year, month, field, section and free-text filters. Crop-program task rows show the derived Phase 13 state and can open `Πρόγραμμα Καλλιέργειας` for editing. Historical records remain read-only projections and are not converted into task rows.

Month names are explicit for each UI language instead of depending on Android/system locale. A Greek profile therefore shows `Ιανουάριος` through `Δεκέμβριος`, not English month names.

## In-app task alerts

The existing Android `Ειδοποιήσεις & Εκκρεμότητες` surface now includes generated crop tasks whose effective state is:

- `overdue` — urgent severity 0;
- `due_today` — attention severity 1;
- `upcoming` within the inclusive seven-day horizon — information severity 2.

Future tasks outside the horizon, completed tasks and skipped tasks do not produce crop-task reminders. The alert list is derived directly from `crop_tasks`; no second persistent queue is introduced and `overdue` is never written into the database.

Selecting a crop-task alert opens the unified calendar focused on the source task. The user can then open the Crop Program page to change the task lifecycle state.

## Boundaries

This checkpoint is in-app only. It does **not** claim background execution, Android notification-channel delivery, alarm scheduling, or reminders while the application is closed. Those concerns remain a later Phase 13 slice and must preserve profile isolation and avoid duplicate notification/task state.

No SQLite schema or backup-format change is required by Phase 13B.

## Verification

Instrumentation coverage checks the read-only Android projection and filters, shared task-state use in alerts, completed-task alert suppression, Greek month labels, menu navigation, and alert deep-linking to a focused calendar. The actual emulator gate must be green before this checkpoint is considered complete.
