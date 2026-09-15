# Phase 13C — Android background crop-task notifications

Phase 13C adds an Android background reminder surface for the crop tasks introduced in Phase 12 and classified by the shared Phase 13 task-calendar semantics.

## Scope

- The existing `crop_tasks` rows remain the only stored task/status source of truth.
- Background reminders are derived from `TaskCalendar`: overdue, due today, and within the next 7 days.
- Stored task status is **not** rewritten to `overdue`.
- In-app `Phase13Alerts` and the Unified Calendar remain available independently of Android system notifications.
- This slice does not add remote push, cloud scheduling, or a second reminder database.

## Scheduling

`CropTaskNotifications` schedules one profile-scoped, inexact `AlarmManager` check for the next local 08:00. The receiver schedules the following check after each run. Inexact alarms are intentional: reminders do not require exact-alarm privileges.

Enabled profile alarms are re-armed when the application starts and after boot, app replacement, clock changes, or timezone changes. Android force-stop semantics still apply: a force-stopped app cannot receive alarms again until the user launches it.

## Permission and privacy

Android 13+ requires `POST_NOTIFICATIONS`. The app asks once, after sign-in, when the profile already contains pending crop tasks. The system permission remains the user's final control. Automated `.checks` builds do not display the system permission dialog; the runtime test grants the permission explicitly when exercising delivery.

Notification content uses `VISIBILITY_PRIVATE`. Tapping a reminder deep-links to the Unified Calendar only while the matching local session is still valid. If the session has expired or the process was restarted, the user is sent to sign-in instead of bypassing the local authentication boundary.

## Deduplication

Each relevant task contributes a token `(generation_key, reminder_state)`. A profile is notified only when a new token appears. This means a task can notify when it first enters the 7-day window, again when it becomes due today, and again if it later becomes overdue, without repeating the same reminder state every day. Completed/skipped tasks disappear from the current reminder set; if a user later reopens the same task as pending, it can become notifyable again.

The token set lives in profile preferences, outside farm backups. It is delivery metadata, not agricultural data.

## Profile isolation

Every alarm and notification is profile-scoped. The receiver resolves the profile through the local profile registry and opens only that profile's farm database. Notification IDs, PendingIntent identities, and deduplication preferences are profile-specific.

## Verification gate

`CropTaskNotificationTest` covers:

- reminder projection for overdue/today/7-day tasks and exclusion of far/completed tasks,
- transition-token deduplication,
- creation and posting of a real Android notification after runtime permission is granted,
- suppression of duplicate delivery for the same state,
- notification channel creation,
- next-local-08:00 alarm timing and cancellation.

The Android runtime workflow includes the new notification production files, manifest, and instrumentation test, so Phase 13C is not considered closed until both normal CI and the API 35 emulator gate are green.
