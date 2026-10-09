# Windows v1 QA Batch 1 — year context and lock core

Classification: DESKTOP. Baseline `4902f566c8e2debfc7eccb67db108424d778dcff`,
`icon-runtime-qa-final`. Existing Money INSERT and Sales product/unit fixes and
their tests were preserved. No Android, schema migration, packaging or commit/push.

The full owner report `WINDOWS_V1_MANUAL_QA_2026-10-03.md` was absent locally and
was read in full through the GitHub contents API at `icon-runtime-qa-final`.
No checkout, pull or remote file replacement was performed.

## Root causes and shared contract

- Physical `year_lock.is_year_locked` aliases were redirected by scanning already
  imported modules at startup. Annual page guards now import
  `year_context.is_year_write_blocked` directly (retaining the local alias for
  compatibility); no module scan or physical-lock function replacement remains.
- `working_context_date(db)` now resolves the owning database's effective year.
  The no-argument UI fallback remains compatible. Month/day projection uses
  `qdate_in_year`, including February 29 clamping.
- Raw date controls and reset paths bypassed the shared default. Annual forms now
  use the helper explicitly. New controls opt into context refresh; Inventory,
  Equipment and Labor identify the relevant edited record so editing their master
  item/worker does not suppress a separate new movement/service/entry default.
- Active-year navigation now permits physically locked years for viewing, displays
  a read-only message and leaves physical locks intact. Mutation warnings direct
  the user to Security / Year Lock / Temporary correction. Correction retains its
  separate prominent state. Success confirmation is centralized and emitted only
  after a real successful active-year transition.
- The locked-year action area has one required reason above temporary correction
  and permanent unlock. Permanent unlock and its reason-bearing audit entry share
  a transaction. Temporary correction remains memory-only, per database, and
  initialization/restart restores physical-lock enforcement.

## Annual call-site disposition

| Owner | Changed boundary |
|---|---|
| Production, Sales, Money | Initial/reset dates; direct effective create/update/delete guards, including original-year checks and locked edit state. Prior Money/Sales fixes retained. |
| Activities | Initial/reset date; effective year in available-year choices; context-refresh opt-in and effective mutation guards. |
| Inventory | Movement initial/reset date and selection-aware context refresh; initial stock date and lock check use effective context; mutation guards remain stock/transaction compatible. |
| Equipment | Purchase/service initial/reset optional defaults; service selection-aware refresh; unused next-reminder date follows service date + six months. Stored dates and enabled reminder choices preserved. Service mutation guards use effective locks. |
| Plant protection, Labor, Plantings | Initial/reset defaults and effective mutation/edit/delete guards. |
| Declaration | Initial available-year/default uses effective year; context callback preserves an existing declaration being edited; save/edit/delete guards honor correction. |
| Invoice documents | Optional date default/reset and effective save/post/delete guards; feature availability unchanged. |
| Alerts | Annual mutation guards only; real-time due/overdue evaluation unchanged. |
| Crop programs | Application year initializes and refreshes to effective year; scheduling default delegates to shared helper. Generation checks season and affected due years, task status checks due year, archive checks pending tasks before deletion. Existing transaction boundaries unchanged. |
| Plant tracking | New dated event defaults to effective year; event writes use shared effective lock guard and show the normal lock guidance. Master plant records remain master data. |

Existing records are loaded using their stored dates. Year-context refresh skips
those editing controls; it does not rewrite database dates. New forms retain their
current month/day during context transitions. Clearing explicitly uses today's
month/day in the effective working year.

## Deliberately retained real-clock calls

The source inventory below lists retained direct clock reads. SQL timestamp
defaults/audit expressions remain real-time metadata, not business-record defaults.

| Call sites | Classification / reason |
|---|---|
| `alerts.py:280`, `equipment.py:485`, `phase13_calendar_integration.py:107` | A: actual today/upcoming/overdue evaluation, not the year in which a record is entered. |
| `audit.py:147,155` | A: initial audit-history timestamp range. |
| `backup_manager.py:83,106`, `pagesbackup.py:105` | A: backup filename and daily backup scheduling timestamps. |
| `data_export.py:530,560`, `exporters.py:59,336`, `upload_center.py:551` | A: export creation time, filename or generated metadata. |
| `invoice_documents.py:249` | A: OCR candidate plausibility relative to the real calendar; never substitutes a stored date. |
| `invoice_documents.py:619,625` | A: archive generated time and filename. |
| `profile_manager.py:301,657` | A: trash/archive timestamp and profile export creation metadata. |
| `data_quality.py:524,671,774,862` | A: detect dates genuinely in the future for Production, Protection, Labor and Plantings; reporting/quality policy is unchanged. |
| `sensor_view.py:33`, `sensor_ingest.py:78` | A: local reading freshness and SQLite ingestion metadata; synthetic working years must not alter these real-time values. |
| `sensor_data_store.py:149,195,258,281,293` | A: local SQLite record/revision/tombstone timestamps. |
| `crop_program_store.py` calls to `time.time` in save_program/save_rules/generate_for_field/set_task_status/archive_program | A: created/updated/generated metadata, distinct from season/due dates. |
| `plant_tracking_store.py` calls to `time.time` in save_plant/append_event/delete_plant/restore_plant | A: record/event creation and tombstone metadata, distinct from event date. |
| `gis/store.py:85,133,158,175`, `gis/sync_repository.py:94,122,196` | A: actual revision/deletion/conflict timestamps (`time.time_ns`). |
| `year_context.py:77,239,253,258,259` | Shared policy: first-use profile-year fallback and real month/day anchor; only the year is projected for annual defaults. |
| `widgets.py:75` | Compatibility detection for callers resetting a new date input to today; the resulting default is the owning effective year. |
| `date_preferences.py:89` | Month/day recurrence reference calendar uses a nearby leap year; not an annual record year. Display preferences are out of scope. |
| `year_lock.py:303`, `year_lock_robustness.py:30` | Management year choices include the physical current year; EnhancedYearLockPage separately includes and defaults to the active year. |
| `products.py:183,318` | Optional master product-field cultivation metadata default/fallback, not an annual posting or lock-controlled journal. Existing link dates are preserved; master behavior is unchanged. |
| `annual_report.py:283` | B, explicitly deferred: read-only report year fallback. Annual Report/report aggregation is excluded from Batch 1. |
| `pagesbackup.py:531` | B, dormant legacy duplicate page: no application import/reference found. Its date_input reset retains the existing shared compatibility behavior; do not revive/refactor the unused page. |

All `CURRENT_TIMESTAMP`, `datetime('now',...)`, SQL epoch timestamps and timer /
performance clocks were left unchanged: they record real creation/update/audit,
backup/sync activity or elapsed time. Canonical record dates and IDs are unchanged.

The referenced sensor clocks serve local agricultural records, not application
telemetry or analytics. Permanent policy: **NO telemetry / NO analytics /
NO advertising / NO behavioral tracking / NO automatic diagnostic upload /
NO automatic outbound reporting.**

## Verification and limits

New `test_year_context_core`: ten tests, including nine annual-page subcases and
both Money kinds. Covers the owner's A–O contracts, leap day, database isolation,
real stored-row editing, cancellation, and additional crop/event lock boundaries.

Focused modules: year_context_core (10), alpha2_step3_year_context (12),
phase16j_year_correction (6), phase16j_exit_correction_localization (7),
phase16j_composed_ui_localization (33), transaction_integrity (32),
inventory_ledger_contract (7), inventory_expense_atomicity (5),
equipment_maintenance_contract (1), crop_program_store (5), crop_program_ui (9),
plant_tracking_store (4). **131 PASS; 0 failures/errors; 0 ResourceWarnings.**

The first focused run had one obsolete assertion expecting locked-year navigation
rejection / no success message. Updated only to the newly approved behavior;
physical-lock, raw-value, button-default and EL/EN/EL assertions remain. Removed
the exit test's patch of the deleted import-time guard hook. The existing Sales
warning mock now includes its actual unit field from the preserved Sales fix.

Closure verification (2026-10-04): the plant-tracking and sensor startup fixtures
now preserve and restore `app.crop_programs.CropProgramsPage` and `RuleDialog` in
their existing `finally` blocks, alongside all existing integration-symbol cleanup.
Their installers previously left a stub page factory in the module, contaminating
the later year-context test. Production behavior and year-context assertions are
unchanged. Both exact startup -> year-context same-process regressions: **2/2 PASS
each**. Complete year-context module: **10/10 PASS**; plant UI module: **5/5 PASS**;
sensor UI module: **4/4 PASS**. All closure focused runs: **0 ResourceWarnings**.

Retained previous complete Desktop discovery: **697 tests; 696 PASS; 1 unrelated
fixture-contamination ERROR; 0 failures/skips; 0 ResourceWarnings**. The exact slow
theme-switch test completed successfully in that run. A subsequent unfiltered
retry was interrupted on owner instruction and is not counted as completed evidence.

New result: **Desktop discovery excluding one previously-passed unchanged slow
theme test: 696/696 PASS in 666.875 seconds; 0 failures/errors/skips;
0 ResourceWarnings**. The only excluded test ID was:
`tests.test_theme_switch_performance.ThemeSwitchPerformanceTests.test_full_tree_switch_still_converts_and_restores_local_style`.
No other test was excluded; normal discovery order was preserved, and the other
theme-module test ran and passed. This is not a new literal 697/697 full run.
**Batch 1 regression verification is closed using this owner-approved combined
evidence.** Theme performance remains deferred to the later Performance batch.

Commands use Python 3.14
`-B -X utf8 -`, offscreen Qt and a fresh temporary `MASTIXA_DATA_HOME`; focused
selection uses `loadTestsFromName('tests.' + module)`, full selection uses
`unittest.defaultTestLoader.discover('tests')` with ResourceWarnings visible.

No installed-build/visual owner retest or Android execution is claimed. Direct SQL
outside guarded workflows is not a database-wide authorization boundary. Read-only
report/dashboard aggregation, default annual list filtering, display formatting,
financial sync and all later QA batches remain separate work. Selecting a locked
year does not erase history or imply those report issues are fixed. No migration
or backup format change; no production data or original dirty checkout touched.
