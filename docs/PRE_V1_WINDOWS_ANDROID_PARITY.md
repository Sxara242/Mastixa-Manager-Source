> Retained historical engineering record, sanitized for public review.
> Current status: [RELEASE_STATUS.md](RELEASE_STATUS.md). This record does not
> establish approval of the current source or a new binary release. Local-only
> receipt paths refer to privately retained evidence, absent from this snapshot.

# Pre-v1.0 Windows / Android parity audit

## FINAL PARITY RERUN — 2026-09-29

Classification: **SHARED (DESKTOP + ANDROID), verification/documentation only**.
Baseline: `8a06f95ae8e0604779dd47c47f4e52f5708db3da`
(`Isolate invoice attachments by profile`), branch `icon-runtime-qa-final`.
Pre-flight: clean working tree, correct approved worktree, `diagnostics/` absent.
This section supersedes the historical checkpoint statuses below without erasing
the original failures or their repair evidence.

### Current-source contract review

- **B1:** `product_registry.ensure_production_stock` sums all fields/years by
  product ID, excludes the edited/deleted row, and tests both old and proposed
  product totals against sales with tolerance `0.000001`. Production page year
  checks precede the guard. Existing valid IDs own renamed/inactive history;
  legacy link repair remains in normal page initialization/refresh. Rejection is
  read-only; complete warning templates are translated before raw interpolation.
  The 13 `test_stabilization.test_production_stock_*` cases cover reductions,
  deletion, exact equality, multiple rows, old/target product reassignment,
  independence, history, tolerance, year precedence and whole-DB preservation.
  Android `ProductionStore` also uses product-level availability and the same
  tolerance inside its transactions. Android forbids changing an existing row's
  product and editing imported history; Windows permits a safe reassignment.
  These explicit editing policies do not change the shared stock invariant.
- **B2:** all eleven converted Windows entry points still use
  `Database.transaction()` for the six linked workflows: sale/income,
  activity/consumption, protection/consumption, receipt/expense,
  service/expense/meter, and invoice posting. `_sync_income(db=tx)`,
  `inventory_sync` and `expense_sync` use the passed connection-bound facade;
  no independent connect/commit was found inside those boundaries. Existing
  triggers remain inside that transaction. The 28 transaction regressions cover
  first/later SQL failures, Python exceptions, create/edit/delete, retry,
  independent persisted snapshots, one commit, rollback and closed handles.
  Android `ProductionStore`, `ActivityStore`, `InventoryStore`, `WorkStore` and
  `DocumentStore` use begin/success/finally-end transactions; their helpers use
  the same store database, including nested SQLite transaction scopes.
- **B3:** `invoice_storage`, `invoice_documents`, `profile_manager` and
  `data_export` were reread. The page database selects owned storage, reads may
  fall back to validated legacy files, and deletion never targets that fallback.
  Same-profile references preserve the owned file until the last row is removed.
  V2 requires exactly the referenced members; V1 without references imports,
  otherwise only safe legacy bytes may be copied, with missing bytes rejecting
  import. Validation/extraction/registration failures clean staging; export
  replaces its destination only after successful completion/validation.
  The 34 ownership regressions include both cross-profile deletion directions,
  identical filenames, restart/switch/hash preservation, fresh-root import,
  archive attacks/limits, failed destination preservation, backup and trash.
  Android `DocumentStore` keeps attachment bytes/hash in each profile database;
  `LocalBackup` includes and validates them. Windows V2 and Android logical
  backups are different formats, not a binary interchange contract.

### Shared-domain classification at this HEAD

**PARITY VERIFIED** below means the supported contract matches in current source
and reviewed regression coverage, with fresh Windows execution reported below.
It does **not** mean Android instrumentation ran in this rerun or that every
possible workflow/edge case was exhaustively tested. Android test owners below
are source/compiled coverage only.

| Domain | Current classification and supporting owners / boundary |
|---|---|
| Profiles, settings, language/session | PARITY VERIFIED for per-profile DB and EL/EN ownership (`ProfileManager`, `ProfileStore`, `UserSession`, `ProfileStoreTest`, `ProfileFlowTest`). INTENTIONAL DIFFERENCE: PIN versus credentials/timed session, separate preferences/credential backups. |
| Fields/parcels | PARITY VERIFIED for fields, area, KAEK/location/tree metadata (`fields.py`, `FarmStore`, catalog fixtures). INTENTIONAL DIFFERENCE: guarded hard deletes versus retained tombstone/history; names/KAEK are not portable IDs. |
| Products | PARITY VERIFIED for registry identity, units, active/history and unique product-field links (`product_registry.py`, `products.py`, `CatalogStore`, `CatalogTest`, stabilization). Local integer/UUID representations differ. |
| Partners | PARITY VERIFIED for supplier/buyer/both and linked historical identity (`partners.py`, `partner_links.py`, `PartnerStore`, `PartnerTest`). Delete representation differs intentionally. |
| Production | PARITY VERIFIED for B1's product-level invariant; Android imported-row/product reassignment restrictions are explicit platform policy, not field/year stock allocation. |
| Sales | PARITY VERIFIED for stock guards and one linked income; B1/B2 tests and Android `ProductionTest` cover lifecycle/rollback. |
| Money/income/expenses | PARITY VERIFIED for linked posting and source ownership (`money.py`, `expense_sync.py`, `MoneyStore`). INTENTIONAL DIFFERENCE: separate Windows tables versus Android kind discriminator. |
| Inventory | PARITY VERIFIED for signed canonical movements, non-negative balance, unit/history protection and source provenance (`inventory_sync.py`, `InventoryStore`, ledger/provenance/atomicity tests). |
| Farm activities | PARITY VERIFIED for canonical category/status, completed-fertilization consumption and descriptive cost (`activities.py`, `ActivityStore`, `ActivityProjection`). Display mapping leaves stored Greek values/raw text intact (`ActivityDisplayLabels`, calendar localization tests). |
| Plant protection | PARITY VERIFIED for source-owned consumption, linked rollback and preserved legacy details (`plant_protection.py`, `WorkStore`, `WorkTest`). Hidden Windows authorization entry does not discard retained data. |
| Labor/workers | PARITY VERIFIED for positive hours/rates, native computed cost, inactive history and imported historical cost (`labor.py`, `WorkStore`, `WorkTest`). Exhaustive cross-runtime rounding is not certified. |
| Plantings/tree tracking | PARITY VERIFIED for batches, additive replantings, optional individual trees/events and separate living totals (`PlantingHistory`, `PlantTrackingStore`, shared Phase14 fixture). |
| Equipment/maintenance | PARITY VERIFIED for service/expense/meter lifecycle and 30-day/50-unit reminder thresholds (`equipment.py`, `WorkStore`, equipment tests, `ReportsLocksTest`). |
| Invoice/documents/OCR | PARITY VERIFIED for ownership, linked finance, bytes in the portable recovery mechanism and reviewed OCR suggestions. INTENTIONAL DIFFERENCE: external Tesseract versus bundled Android engine, owned files versus DB bytes, 20 MiB Windows archive-member versus 5 MiB Android document limit. Actual OCR/pickers are EXTERNAL/DEVICE-LIMITED here. |
| Crop program | PARITY VERIFIED for shared fixed-date/daily-window rules, deterministic keys and preservation of completed/skipped tasks (`crop_program.py`, `CropProgram`, stores, Phase12 fixture). Advanced Windows recurrence/persistent field links remain WINDOWS-ONLY, U2. |
| Calendar/tasks | PARITY VERIFIED for read projections, canonical status and derived overdue/today/7-day states (`task_calendar.py`, `TaskCalendar`, `UnifiedCalendarStore`, Phase13 fixture). Generation does not post completed work or money. |
| Alerts/notifications | PARITY VERIFIED for supported derived in-app alerts. Background profile-routed task delivery is ANDROID-ONLY (`CropTaskNotifications`), with OS/permission/OEM delivery UNVERIFIED. |
| Year locks | PARITY VERIFIED for supported page/store dated workflows, old/new-year protection and linked rollback. INTENTIONAL DIFFERENCE: Windows page guards/temporary correction versus Android SQL triggers (`YearLocks`, year-context tests, `ReportsLocksTest`). Not a blanket direct-SQL/concurrent-writer guarantee on Windows. |
| Reports | PARITY VERIFIED for inspected posted totals, all-time stock versus period reports, field operational cost and source-money counting (`reports.py`, `field_finance.py`, `ReportStore`, report consistency/locks tests). Layout and export rendering differ; arbitrary numeric edges remain unverified. |
| GIS/coordinate export | PARITY VERIFIED for original geometry/declared CRS plus derived WGS84, ordered rings/parts and explicit export modes (`gis/exports.py`, `CoordinateExport`, reference/shared tests). Shapefile/DXF conversion is WINDOWS-ONLY; physical GNSS is ANDROID-ONLY and DEVICE-LIMITED. |
| Backup/restore | PARITY VERIFIED for each documented recovery contract, INTENTIONAL DIFFERENCE in artifact semantics; see U3. Android schema-18 logical snapshot covers 34 listed tables, not its separate credential registry. U1 remains deferred. |
| Import/export | PARITY VERIFIED for the supported Windows subset CSV/ZIP-to-Android and explicit document/geometry packages (`data_export.py`, `CatalogImport`, `DocumentPackage`, import fixtures). Full bidirectional farm transfer and cross-platform binary backup compatibility are not supported claims. |
| Offline/sync | PARITY VERIFIED for local core data and inspected GIS revision/conflict protocols (`FarmStore`, `GisSyncRepository`, shared sync tests). Pending rows are not automatic network delivery. General business adapters/online backup are FUTURE; live Supabase/RLS is UNVERIFIED EXTERNAL. |
| Sensors | PARITY VERIFIED for canonical metrics/units, timestamp/status and shared projections (`SensorData`, stores, Phase15 fixture); actual providers are UNVERIFIED EXTERNAL. |

### U1 / U2 / U3 revisited

- **U1 — FUTURE/DEFERRED; populated-registry restore still UNVERIFIED.** Current
  Android `LocalBackup.TABLES` still omits `activity_sync_fields` and
  `activity_sync_sources`. Production search found only registration definitions,
  not registration calls; `ActivityProjection` reads mappings when present.
  Thus this remains a real precondition before enabling business sync adapters,
  not a newly demonstrated failure in an enabled user workflow. Decide and test
  backup/replacement/clearing semantics before activating those adapters.
- **U2 — WINDOWS-ONLY today; Windows v1 scope decision ACCEPTED.** Current
  Android Rule still contains only fixed date/daily intervals. Windows supports
  week/month/once intervals, multi-year/base-year recurrence, persistent field
  links, active-year context and temporary correction. The owner accepts Windows
  v1 proceeding without exact Android feature parity; these gaps do not block
  Windows v1. Android functional parity remains future work, detailed below.
- **U3 — RESOLVED as a documented capability distinction.** Windows SQLite backup
  is database-only; in-place restore keeps files still present but cannot recover
  deleted attachment bytes. Windows V2 full profile export carries all referenced
  attachments for fresh-install import, with failure instead of missing bytes.
  README explicitly states this and old-release incompatibility. Android logical
  backup includes `DocumentStore.COLUMNS` attachment/hash and validates them in
  staging. Its 50 MiB backup/5 MiB attachment limits and separate credentials are
  distinct policies. No binary archive compatibility is claimed.

### Android U2 TODO plan — accepted scope checkpoint

Planning only, based on the existing parity/progress documentation; no new source
audit or test execution. Windows v1 does not require exact Android feature parity.
Future Android work should match business rules, supported workflows and data
contracts; UI, storage representation and enforcement architecture may differ.
Every item below is **TODO / not implemented by this checkpoint**. Phase labels
are proposed future batches, not authorization to start or a new release gate.

| Feature | Documented Windows behavior | Documented Android status | Functional parity target | Shared data / business-rule impact | Recommended future phase |
|---|---|---|---|---|---|
| Weekly recurrence | Week-based within-period recurrence, using `within_period_unit` / `within_period_interval`. | Rule model supports shared fixed-date/daily intervals, not the advanced unit fields. | Match Windows weekly occurrence dates and interval semantics; retain deterministic task keys and completed/skipped state. | Yes: schedule semantics and generated task identity; never approximate as `everyDays`. | A1 — advanced crop recurrence contract and implementation. |
| Monthly recurrence | Month-based within-period recurrence. | No matching advanced month-unit model documented. | Match Windows month-boundary and interval behavior, including its actual edge-date policy; establish fixtures before implementation. | Yes: calendar calculations and task generation; a month must not be coerced to a fixed day count. | A1 — advanced crop recurrence. |
| Once-per-window recurrence | `once` within-period option. | No matching advanced `once` option documented; existing fixed-date support is not proof of equivalence. | Match Windows selection of the single occurrence in a window and regeneration behavior. | Yes: occurrence count, date and stable task identity. | A1 — advanced crop recurrence. |
| Multi-year / base-year recurrence | `every_years` and `base_year` anchor recurring windows across years. | These fields exceed the current Android Rule/Store model. | Select the same eligible years/windows using the same anchor and interval; preserve existing fixed/daily rules. | Yes: rule representation, year eligibility and generated task dates. | A1 — advanced crop recurrence. |
| Persistent program-to-field links | Persistent `crop_program_field_links`. | Matching persistent links exceed the documented Android Rule/Store model. | Retain program/field associations across reopen and recovery, generate tasks for the linked fields, and preserve existing completed/skipped tasks. | Yes: relationship identity, generation scope and backup/import preservation; never infer field identity from names. | A2 — persistent crop-program field associations, after A1. |
| Active-year context | Windows exposes an active-year context. | No matching active-year workflow documented; Android dated-record lock enforcement already exists. | Match the Windows active-year workflow and its effect on supported operations without changing record dates or weakening existing locks. | Yes: workflow year selection and interaction with dated-record guards. | A3 — year-context workflow, before temporary correction. |
| Temporary locked-year correction | Explicit temporary correction of a locked year, separate from the active year. | No matching temporary-correction workflow documented; SQL triggers enforce dated-table locks. | Provide equivalent bounded correction and exit behavior while preserving active-year context, user reason text, old/new-year checks and linked-write atomicity. | Yes: write authorization and lock lifecycle; Android need not copy Windows page-guard architecture. | A4 — temporary correction, after A3; define safe trigger interaction before implementation. |
| Date-display preferences (profile-area U2 difference) | Windows date-display preferences are documented in the profile/session matrix. | No matching implementation documented. | Offer equivalent supported display choices while keeping canonical stored dates unchanged; inventory exact Windows options in the future batch. | Presentation/preferences only; no canonical date or business-rule changes. | A5 — profile date presentation, independently scoped after year-context contracts are settled. |

Future acceptance should use Windows-derived contract fixtures, preserve existing
IDs/canonical values/history, and cover persistence plus backup/import handling
where the new capability stores state. Android connected-device verification must
be planned explicitly; the earlier compilation-only evidence does not satisfy it.
This plan does not select a schema/migration design or promise cross-platform binary
archive compatibility. U1 adapter backup, U3 artifact semantics, GIS formats and
other platform differences are not expanded into this U2 implementation backlog.
Historical statements that U2 awaited owner scope acceptance are superseded here;
Android delivery timing remains future planning, not a Windows v1 blocker.

### Fresh execution evidence

**Windows: all completed runs PASS, zero failures/errors/skips and zero
ResourceWarnings (including SQLite).** Results were recovered after interruption;
no unfinished run is counted as passed and no completed gate was rerun.

Execution used Python 3.14 at
`<USER_HOME>\AppData\Local\Programs\Python\Python314\python.exe`, invoked
as `python.exe -B -X utf8 -` with a PowerShell stdin runner,
`QT_QPA_PLATFORM=offscreen`, and a fresh `TemporaryDirectory` assigned to
`MASTIXA_DATA_HOME` before application imports. Runners captured ResourceWarnings
and forced garbage collection before counting them. No real profile was used.

| Completed run | Loader / equivalent unittest selection | Result |
|---|---|---|
| Focused integration | `loadTestsFromName('tests.' + module)` in the table order below, combined `TestSuite`, `TextTestRunner(verbosity=2)` | **213 PASS**, 1600.592s, exit 0 |
| Standard desktop discovery | `unittest.defaultTestLoader.discover('tests')`, `TextTestRunner(verbosity=2)`; same selection as `python -m unittest discover -s tests -v` | **683 PASS**, 3016.256s, exit 0 |
| Isolated profile-switch diagnostic | `loadTestsFromName('tests.test_profile_switch_ui')`; equivalent selection `python -B -m unittest tests.test_profile_switch_ui -v` | **3 PASS**, 17.785s, exit 0 |

Exact focused module inventory (all under `tests.`):

| Module | PASS |
|---|---:|
| `test_stabilization` | 23 |
| `test_transaction_integrity` | 28 |
| `test_inventory_ledger_contract` | 7 |
| `test_inventory_expense_atomicity` | 5 |
| `test_inventory_quality_gate` | 3 |
| `test_equipment_maintenance_atomicity` | 4 |
| `test_equipment_maintenance_contract` | 1 |
| `test_phase16e_cross_module_validation` | 2 |
| `test_activity_projection` | 34 |
| `test_report_consistency` | 1 |
| `test_alpha2_step3_year_context` | 12 |
| `test_phase16f_realistic_performance` | 1 |
| `test_invoice_profile_ownership` | 34 |
| `test_profiles` | 5 |
| `test_phase16i_security` | 10 |
| `test_phase16d_backup_restore` | 7 |
| `test_profile_switch_ui` | 3 |
| `test_phase16j_composed_ui_localization` | 33 |
| **Total** | **213** |

The 23 stabilization tests include **all 13 B1 invariant cases**. Counts overlap
across runs: the full suite has **683 distinct tests**, not 899. All remaining
profile-switch and composed-localization cases completed. In isolation,
`test_hot_switch_survives_all_delayed_icon_refreshes`,
`test_report_navigation_uses_matching_optimized_icons`, and
`test_startup_chooser_unlocks_pin_and_area_is_compact` all passed.

The delayed profile-switch case also passed in the custom order and standard
discovery: no permanent hang or regression was demonstrated, and no test-harness
or production adjustment was needed. Full-run non-terminating faulthandler samples
showed Qt event processing and later database setup while the suite continued;
these diagnostic timeout dumps were not test failures. The exact slowdown cause
was not isolated; overlapping runs are not a controlled performance comparison.
Expected injected rollback/profile-switch exception logs belonged to passing
failure-path tests. Full discovery's captured warning categories were empty.

Android command (existing JDK 21/SDK 36, normal user Gradle cache):

```text
.\gradlew.bat testDebugUnitTest lintDebug assembleDebug assembleChecksAndroidTest --console=plain
```

**BUILD SUCCESSFUL, 32s; 95 actionable tasks: 13 executed, 82 up-to-date.**
`testDebugUnitTest`: **NO-SOURCE (zero local unit tests executed)**.
Lint: **0 errors / 11 warnings**. Debug APK assembly and checks-instrumentation
APK compilation/assembly passed. Existing deprecated MainActivity API and Gradle
9-incompatibility notices remain; no dependency/build configuration was changed.
`adb devices -l`: empty connected-device list. Therefore **Android instrumentation
runtime execution remains UNVERIFIED in this rerun**. No emulator was launched,
no application installed, and no physical-device evidence is asserted.
Initial sandbox execution restrictions were resolved by approved elevated tool
execution and the existing user Gradle cache; these were not test failures.

### Limits and checkpoint decision

**SUPPORTED-WORKFLOW PARITY VERIFIED FOR THIS CHECKPOINT.** B1 (stock invariant),
B2 (atomic linked writes), and B3 (profile-owned attachments/archive recovery)
are **VERIFIED FIXED** by current-source comparison and passing Windows execution.
No new material parity defect was demonstrated. This closes the requested rerun,
not every device, external-service or eventual v1 feature-scope obligation.

Evidence levels remain separate:

1. **Source/static:** supported Windows/Android contracts and test owners reviewed;
   domain classifications and exceptions are recorded above.
2. **Desktop automated:** 683/683 full-suite PASS; focused 213/213 and isolated
   profile-switch 3/3 PASS, with zero ResourceWarnings.
3. **Android JVM/Gradle:** build/lint/instrumentation compilation PASS;
   JVM unit task NO-SOURCE, so zero JVM tests executed.
4. **Android connected-device:** NOT RUN, no connected device; runtime validation
   remains pending and cannot be inferred from compilation or Windows tests.
5. **External/environment-dependent:** limitations below remain unverified.

U1 remains deferred until adapter activation; U2 is accepted as non-blocking for
Windows v1 with future Android TODOs above; U3 is a documented recovery-artifact
distinction. The documentation
checkpoint is ready for review/commit, but no commit/push is performed. Exact next
action: **DEEP CROSS-FEATURE REAL-WORLD USAGE AUDIT**, followed by the final pre-v1
verification/release gate. Neither starts in this checkpoint.

Physical GNSS accuracy/power, arbitrary SAF/camera providers, real OCR engines,
OEM notification delivery, live map/tile/Cadastre providers, configured
Supabase/RLS, concurrent filesystem adversaries, old OS quirks and arbitrary
cross-runtime rounding remain outside this rerun's evidence. Generated Android
build/cache outputs remain ignored; no artifacts are included in the Git diff.
No production/test/schema/migration/dependency/licensing change is made here.
The Deep Cross-Feature Real-World Usage Audit has not started. Phase16I remains
independently PARTIAL / owner-deferred; this is not public-release approval.

## Historical first audit and fix evidence

Date: 2026-09-28. Classification: **SHARED (DESKTOP + ANDROID)**.

Documentation closure reviewed: 2026-09-29. The first audit checkpoint is
**research-complete / formally closed**; this does not close its unresolved defects.
**Status: PARTIAL. B1/B2/B3 are FIXED / pending final Windows / Android parity rerun.**
This is a source/contract audit with focused synthetic execution, not full device QA.
The original audit made no production changes. The scoped B1/B2/B3 follow-ups are recorded
below; no schema change or migration was added.

## Baseline and evidence rules

- Audited HEAD: `762223f3693ca63146d2c869f776c5bf8d09e24f`
  (`Add packaged Windows startup smoke test`).
- Worktree: `<WORKSPACE>\Mastixa-Icon-Diagnosis`;
  branch `icon-runtime-qa-final`. Pre-flight working tree clean; `diagnostics/` absent.
- Owner-supplied retained evidence at this SHA: Verify desktop/Android #356
  SUCCESS; Windows release gate #79 SUCCESS, including real isolated EXE startup.
  These runs were not rerun or independently queried in this audit.
- Read `AGENTS.md`, `MASTER_PROGRESS.md`, `PHASE16J_FINAL_VERIFICATION.md`,
  `PRE_RELEASE_BUG_AUDIT.md`, and `FULL_QA_CHECKLIST.md`. Their historical dates,
  old branches and pending notes are not proof of current implementation state.
- The current `verify.yml` Android command runs unit tests, lint, debug assembly
  and instrumentation **compilation**, not connected instrumentation execution.
- `adb devices` returned no connected devices. Android store/UI tests below were
  inspected, not newly executed. Their presence is coverage evidence, not a new PASS.
- No real databases, backups, credentials or original dirty checkout were used.
  Each reproduction set `MASTIXA_DATA_HOME` to a new temporary directory before
  importing application modules, with Qt offscreen. Temporary fixtures were removed.

Difference classifications: **TRUE PARITY BUG**, **INTENTIONAL PLATFORM DIFFERENCE**,
**WINDOWS-ONLY FEATURE**, **ANDROID-ONLY FEATURE**, **FUTURE / UNDER-CONSTRUCTION**,
**EXTERNAL / DEVICE-LIMITED**, **UNVERIFIED**. A supported common contract can match
without identical SQL schemas, UI layouts, local IDs or backup file formats.

## Parity matrix

Android owners below are in `android/app/src/main/java/gr/mastixa/manager/`;
Windows owners are under `app/`. Test names refer to `tests/` or Android
`src/androidTest/java/gr/mastixa/manager/`. "Match" means the inspected contract,
not an exhaustive guarantee for every input or lifecycle.

| Area | Windows owner / Android owner | Supported contract, classification and evidence limits |
|---|---|---|
| A. Profile, session, settings | `profile_manager.py`, `runtime_paths.py`, `main_window.py`, `date_preferences.py`, `year_context.py` / `ProfileStore`, `UserSession`, `MainActivity` | Per-profile DB ownership and EL/EN language are supported on both. Windows JSON registry/default and UUID profiles/PIN differ intentionally from Android credential registry, legacy profile, UUID DB filenames and timed in-memory session. Profile credentials are outside Android farm backups. Windows active-year/correction/date-display preferences have no matching Android implementation: current Windows-only capability; v1.0 scope acceptance remains U2. **TRUE BUG B3** breaks Windows attachment ownership after profile copying. Existing `test_profiles`, `test_profile_switch_ui`, `ProfileStoreTest`, `ProfileFlowTest`, `SessionPolicyTest` do not prove attachment independence. |
| B. Producer, fields, products, partners | `database.py`, `fields.py`, `product_registry.py`, `products.py`, `partners.py`, `partner_links.py` / `FarmStore`, `CatalogStore`, `PartnerStore`, `CatalogImport` | Common producer contacts, KAEK/location/area/tree metadata, product names/units/active flags, unique product-field association and supplier/buyer/both semantics. Windows integer IDs and Android UUID/local imported IDs are **INTENTIONAL PLATFORM DIFFERENCES**, not interchangeable identifiers. KAEK/name is not portable identity. Windows referentially guarded hard deletes versus Android tombstones/history are distinct storage policies. Imported-history restrictions are explicit in Android stores/UI. `CatalogTest`, `PartnerTest`, `test_stabilization` inspect identity, links and legacy behavior; no new full CRUD matrix run. |
| C. Production, sales, money | `production.py`, `sales.py`, `money.py`, `expense_sync.py` / `ProductionStore`, `MoneyStore`, `ProductionImport` | Shared product availability and one linked income per sale; Android combined `money_entries` maps Windows `income`/`expenses`. **TRUE BUG B1:** Windows harvest reduction/deletion can leave oversold stock. **TRUE BUG B2:** Windows sale/income commits can split on failure. Android explicitly checks stock and wraps linked changes in transactions; `ProductionTest.localStockIncomeLifecycleAndRollback` covers both. Normal Windows sale lifecycle is covered by `test_stabilization`, but that is not rollback proof. |
| D. Inventory | `inventory.py`, `inventory_sync.py`, `expense_sync.py`, `inventory_report.py` / `InventoryStore`, `MoneyStore`, `InventoryImport`, `ReportStore` | Canonical `Παραλαβή`, `Κατανάλωση`, `Διόρθωση +`, `Διόρθωση -`, signed stock, source provenance, receipt expense linkage and non-negative balance contracts align. Windows triggers guard deletion/unit history and receipt-expense atomicity; Android transactions enforce store ownership and imported-row restrictions. Local source encodings (`farm_activity` versus `android_farm_activity`, local IDs versus `windows_id`) are intentional adapters. Shared provenance tests passed here (2); ledger/atomicity/quality tests inspected, not all rerun. Automatic activity/protection consumption has **B2** on Windows. |
| E. Irrigation / fertilization | `activities.py`, `activity_projection.py`, `activity_identity.py`, `farm_calendar.py` / `ActivityStore`, `ActivityProjection`, `ActivityIdentityRegistry`, `ActivityDisplayLabels`, `UnifiedCalendarStore` | Greek canonical categories/statuses remain persisted; labels are presentation only. Completed fertilization consumes inventory; irrigation needs duration or water; costs are descriptive rather than automatic cash posting. Both retain source detail/projection identity. **B2** affects failure atomicity. Portable identity fixture passed here (1), with no invented identity from names/KAEK. Activity registry backup coverage remains U1. Closed localization work was not reopened. |
| F. Plant protection | `plant_protection.py`, `inventory_sync.py` / `WorkStore`, `WorkImport` | Field, product, ingredient, legacy authorization, dose/unit, quantity, harvest interval and cost are supported. Windows hides authorization entry while retaining legacy content; hiding a retained field is an **INTENTIONAL PLATFORM DIFFERENCE**, not evidence of data loss. Shared source-owned consumption and year checks exist. **B2** leaves a Windows protection record without consumption on injected failure. Android `WorkTest` covers related atomic source writes; no fresh instrumentation run. |
| G. Labor / workers | `labor.py` / `WorkStore`, `WorkImport` | Workers, active/history restrictions, positive hours, rates, computed native cost and historical imported costs are represented. Android imported rows are explicitly read-only. Work costs are operational report inputs, not automatically duplicated cash expenses. Inspected `WorkTest`, `WorkUiTest` and Windows cross-module/stabilization coverage. Detailed rounding/legacy edge equivalence is **UNVERIFIED** at runtime in this audit. |
| H. Plantings / trees | `plantings.py`, `planting_history.py`, `plant_tracking.py`, `plant_tracking_store.py` / `WorkStore`, `PlantingHistory`, `PlantTracking`, `PlantTrackingStore`, `PlantTrackingBackup` | Both have batches, planted/alive totals, additive replantings and optional individual trees/events (`active/dead/removed`, health and note/status events). Replantings cannot predate the batch; tracking does not silently replace batch totals. Common tree contract tests passed (3). Desktop SQLite backup includes these tables; Android logical backup includes tree/event/replanting tables with old-schema clearing tests. Windows generic CSV export lists batches, not every later tree registry: subset interoperability, not full farm transfer. |
| I. Machinery / maintenance | `equipment.py`, `expense_sync.py` / `WorkStore`, `EquipmentImport` | Equipment, hours/km/none meter, service history, next-date/meter reminder and linked expense supported. Windows equipment/expense triggers and Android transaction/queue handling differ intentionally. Existing `test_equipment_maintenance_contract`, `test_equipment_maintenance_atomicity`, `EquipmentTest`, `ReportsLocksTest` cover meter history, one expense, rollback and lock handling. Threshold wording/source agree on 30 days/50 meter units. No new service lifecycle execution here. |
| J. Documents / OCR | `invoice_documents.py`, `profile_manager.py`, `data_export.py` / `DocumentStore`, `DocumentPackage`, `DocumentImport`, `OfflineOcr` | Both store metadata, financial references and export attachment packages; OCR produces suggestions needing review. Windows uses external Tesseract when present; Android bundles an offline OCR engine and uses device document selection: **INTENTIONAL / EXTERNAL** availability differences. Android attachments are DB-contained; Windows attachments live outside the DB in one application-level directory. This implementation difference causes **B3** after profile copying. Portable attachment completeness and fresh-machine Windows restore remain U3. |
| K. Crop program, calendar, alerts | `crop_program.py`, `crop_program_store.py`, `task_calendar.py`, `farm_calendar.py`, `alerts.py` / `CropProgram`, `CropProgramStore`, `TaskCalendar`, `UnifiedCalendarStore`, `Phase13Alerts`, `CropTaskNotifications` | Common fixed-date/daily interval rules, deterministic generation keys, preservation of completed/skipped tasks and pending/completed/skipped canonical states. Generation plans work; it does not create completed money/inventory/activity records. Shared base-rule/calendar tests passed (6). Android background notifications are **ANDROID-ONLY**, permission/lifecycle limited. Windows Alpha2 multi-year/month/week/once windows and persistent field links exceed Android Rule/storage fields: U2, not a presumed intentional parity exemption. |
| L. Year locks | `year_lock.py`, `year_context.py`, page guards / `YearLocks`, `LocalBackup`, import transactions | Android SQL triggers guard INSERT/DELETE and both OLD/NEW dates for its dated tables; Windows pages check target/original years and allow explicit temporary correction. Enforcement architecture is an **INTENTIONAL PLATFORM DIFFERENCE**; equivalent user-level protection still needs checking for every supported linked path. Windows service/direct-SQL bypass and optional tree/task table coverage are **UNVERIFIED**, not a blanket lock PASS. Android full restore explicitly replaces lock policy transactionally. Tests inspected: `ReportsLocksTest`, `test_alpha2_step3_year_context`, cross-module tests. |
| M. Reports / projections | `reports.py`, `sales_report.py`, `inventory_report.py`, `field_finance.py`, `field_profile.py`, `annual_report.py` / `ReportStore`, `ActivityProjection` | Conceptual financial totals, production, sales/current stock, receipt-weighted inventory value, field cost/card and annual outputs supported. Filter scopes are explicitly different from all-time availability; operational costs and posted expenses can double-count a manually duplicated cost on both clients. Android exports CSV/XLSX/PDF, with literal user values and formula escaping; it is not a pixel copy of Desktop. Existing `test_report_consistency`, `ReportsLocksTest`, `FieldCardProjectionTest` inspected. No new whole-report numeric equivalence PASS; B1/B2 can corrupt report inputs. |
| N. GIS / CRS | `gis/geometry.py`, `store.py`, `importers.py`, `exports.py`, `tracks.py` / `ParcelGeometry`, `GeoStore`, `GeometryImport`, `CoordinateExport`, `GpsTrack` | Original geometry and declared CRS retained separately from normalized WGS84; polygon/multipolygon/ring order, coordinates, field/KAEK attributes, points/tracks and revisions represented. Python pyproj versus Java Proj4J/JTS is intentional; published-reference tests and retained CRS exchange evidence exist. Android explicitly rejects Shapefile/DXF and requests Desktop conversion (**WINDOWS-ONLY import formats**). Physical GNSS, official Cadastre, provider availability and all possible EPSG definitions remain **EXTERNAL / UNVERIFIED**. |
| O. Import / export | `data_export.py`, `invoice_documents.py`, GIS exporters / `WindowsImport`, `CatalogImport`, domain importers, `DocumentPackage`, `CoordinateExport` | Supported direction is Windows subset ZIP/CSV to Android, plus explicit document/geometry formats. Binary DB files are not a cross-platform interchange contract; Android backup JSON is not a Windows SQLite backup. Android preview/apply checks required/duplicate columns, links, finite values, dates, duplicate history, bounded expanded ZIPs and transactional apply with a recovery snapshot. Canonical IDs/values are preserved through explicit mapping, not UI translation. Newer crop/tree/sensor registries are not in generic desktop CSV sections. Generic symmetric farm round-trip is **UNSUPPORTED / UNVERIFIED**, not claimed. Existing real-ZIP import and `Phase16CsvImportTest` coverage inspected. |
| P. Backup / restore | `backup_manager.py`, `profile_manager.py` / `LocalBackup`, feature Backup classes, `ProfileStore` | Windows SQLite online backup copies all DB tables, supports rollback/safety snapshots and profile ZIPs; Android schema-18 logical backup lists 34 tables, including GIS, crop, trees, replanting and sensors, and validates in staging before atomic replacement. Older Android formats intentionally clear absent newer tables on full restore (covered by `LocalBackupTest`); not an incremental merge. Credentials/preferences have separate platform policies. Activity identity registry omission is U1; Windows external attachment coverage/ownership is B3/U3. Not a complete all-feature backup parity PASS. |
| Q. Sync contracts | `gis/sync_contract.py`, `gis/sync_repository.py`, `activity_identity.py` / `GisSyncContract`, `GisSyncRepository`, `ActivityIdentityRegistry` | GIS schema-1 records, explicit dataset context, UUID/parent identity, tombstones, revision/expected-hash conflict checks, CAS retry/lost ACK and pending-parent ordering are implemented on both. Local integer-vs-UUID IDs are not portable identity. Source registries only expose verified `sync_ref`; no runtime business-adapter registration call sites were found beyond definitions. Mock/local contract coverage exists (`test_sync_contract`, `test_sync_repository`, `GisSyncTest`). General business sync and configured live Supabase are **FUTURE / EXTERNAL**, not certified. |
| Additional: sensors | `sensor_data.py`, `sensor_data_store.py`, `sensor_ingest.py`, `sensor_view.py` / `SensorData`, `SensorDataStore`, `SensorDataIngest`, `SensorView` | Matching canonical metric/unit, UTC-second timestamp, status/quality and stale-reading contracts; pure shared fixture tests passed (3). Android logical backup includes all three sensor tables. Actual providers/devices remain **EXTERNAL**. This audit did not provision APIs or infer live telemetry support. |

## Reproduced true parity bugs

### B1 — HIGH: Windows production can invalidate already-sold availability

**2026-09-29 follow-up: FIXED / pending final parity rerun (DESKTOP only).**
Implementation baseline: `a51b01717842d7f6215df2cb332598ab718a85a0`.
`product_registry.ensure_production_stock` checks hypothetical totals before a
production edit/delete writes: `proposed_production + 0.000001 >= sold_quantity`
for both affected product IDs. It excludes the old row and adds the proposed row
only to its target product; deletion adds nothing. Totals follow SalesPage's
all-field/all-year, inactive-history contract. Existing page initialization/refresh
repairs legacy product links; the guard itself is read-only and does not migrate
or rewrite names. Valid IDs take precedence after renaming. Creates and existing
year-lock precedence are unchanged. The warning uses a translated complete template
before interpolating raw product names and quantities, including live EL/EN/EL.

Focused evidence: 13 new cases in `test_stabilization` cover all ten requested
scenarios, both tolerance sides, safe and rejected reassignment, target-product
totals, inactive/legacy history, raw-value localization and unchanged whole-DB
snapshots on rejection. Before implementation, 11 cases ran: **6 expected failures,
5 PASS**. After implementation all 13 distinct cases passed; one extra fixture's
missing required sale price/total was corrected and its test rerun successfully.
The test harness intercepts the language-aware dialog; the separate localization
case exercises the actual modal and live switching. No assertions were weakened.

Closure verification: retained **23/23 stabilization cases PASS** (including the
13 new cases); fresh **15/15 PASS** for `test_alpha2_step3_year_context` (12) and
`ComposedUiTests.test_all_locked_headings_and_edit_state`,
`test_sales_insufficient_stock_product_and_no_write`, `test_catalog_contract` (3).
The two year-context dialog tests also passed **2/2** with an explicitly active
English controller. Total: **38 distinct cases PASS**, plus those two repeats;
no full desktop suite or Android run. Tests used `python.exe -B -X utf8 -` with
`unittest` names above, Qt offscreen and a temporary `MASTIXA_DATA_HOME` set before
imports. Completed stabilization work was not rerun at closure.

The interrupted combined run blocked because existing year-context tests mocked
static `QMessageBox.warning/question` but not the localized `QMessageBox.exec`
path used with an active controller. Both gaps were reproduced with a sentinel
instead of a modal wait. The only closure code adjustment adds scoped `exec`
interception to those two tests; existing assertions and production year behavior
are unchanged. This is not a HIGH #1 regression. The stale test runner was stopped.
Final `git diff --check` passed; no generated artifacts or `diagnostics/`.

This is a pre-write Production guard, not a redesign of linked transactions or a
new cross-process concurrency guarantee. B2/B3 are untouched. The original
reproduction and repair rationale below are retained as historical evidence.

Owners: `app/production.py:179` (`save_production`), `:325`
(`delete_production`), versus `ProductionStore.java:32-45`.

Shared reason: both clients sell only available production; Android also prevents
editing/deleting its source quantity below sales. No documented Desktop exception
was found. Windows sales validates a new sale, but production mutation has no
corresponding balance guard; the only production triggers found are audit triggers.

Synthetic reproduction through real page methods:

1. Create a field/product/buyer; harvest 20; save a sale of 5 through `SalesPage`.
2. Set `ProductionPage.selected_production_id`, keep the same field/product,
   set quantity 4, call `save_production()`.
3. Production becomes **4**, sold remains **5**, balance **-1**.
4. Confirm `delete_production()`: production rows become **0**, sales remain **1**.

Android source rejects both mutations; existing
`ProductionTest.localStockIncomeLifecycleAndRollback` tests reduction 20 -> 4
after selling 5, and deletion rejection. That test was inspected, not rerun.
Windows normal sale lifecycle coverage does not cover this production-side gap.

Required repair: protect original and target product balances during create/edit/
reassignment/delete in a transaction-safe owner boundary, with unchanged sales,
income, raw names, dates and year rules on rejection. Include legacy product links.
No partial UI-only patch was applied in this audit.

### B2 — HIGH: Windows linked business writes are not consistently atomic

Owners: `sales.py:681`, `activities.py:812`, `plant_protection.py:207`;
`database.py:333` opens/commits a connection for each `execute`.
Source row writes and subsequent `_sync_income` / `sync_consumption` use separate
commits. No startup wrapper replacing these methods with one transaction was found.

Synthetic SQLite BEFORE INSERT triggers injected failure into the linked child
write, after valid forms were populated and submitted through real page methods:

| Path | Reproduction output after exception | Required invariant |
|---|---|---|
| Sale -> income | From one valid sale/income, second sale fails to insert income: **2 sales, 1 income, 1 unlinked sale** | Whole second sale rolls back |
| Completed fertilization -> consumption | **1 activity, 0 source consumption rows** | Source and ledger commit/rollback together |
| Protection -> consumption | **1 protection record, 0 source consumption rows** | Source and ledger commit/rollback together |

Android `ProductionStore.saveSale`, `ActivityStore.save`, and
`WorkStore.saveProtection` use `beginTransaction` / successful commit / finally
endTransaction around linked changes. `ProductionTest`, `ActivityTest` and
`WorkTest` contain rollback/relationship regressions; new Android runtime execution
was unavailable. Windows inventory-receipt and equipment-expense trigger protections
are different, already-covered paths; they do not fix these three owners.

Required repair: narrowly establish a single transaction for each source and child
write (including edit/delete), then inject failures at both sides and assert full
snapshot preservation. Do not claim ordinary idempotence tests prove atomicity.
No transaction architecture was changed during this audit.

#### B2 follow-up — 2026-09-29 (DESKTOP)

**HIGH #2: FIXED / pending final parity rerun.** Clean pre-flight baseline
`4c05d6fd4671853ec86d3584821153357e278e4b`, branch `icon-runtime-qa-final`.
The historical reproduction above remains evidence of the original defect.

Confirmed logical operations now use one explicit `Database.transaction()`:

| Owner | Boundary and transaction-bound helpers |
|---|---|
| Sales | Create/edit sale, `_sync_income(db=tx)`, income link; delete income + sale |
| Activities | Create/edit record + `sync_consumption(tx)`; delete consumption + record |
| Plant protection | Create/edit record + `sync_consumption(tx)`; delete consumption + record |
| Inventory receipts | Create/edit movement, trigger-owned expense, `sync_expense(tx)`, expense link; delete through `delete_expense(tx)` + movement |
| Equipment maintenance | Create/edit service, expense projection/link and meter update; delete service + expense |
| Invoice financial posting | Income/expense INSERT + document financial-reference UPDATE; no attachment/filesystem operations |

Receipt/service triggers already protect individual source statements, but later
UI writes could previously fail after that commit. Existing triggers and helper
business rules are unchanged. All queries/writes inside each new boundary use its
single connection. Helpers cannot call commit/connect/nested transactions through
the yielded facade. Normal deferred `BEGIN`; one commit on success; exception
rollback and handle closure through existing `_ClosingConnection`. Standalone
`Database.execute()`, FK/PRAGMA/journal settings, and validation/year checks remain
unchanged. No global or thread-local transaction state.

Discovery classification: the six operations above are linked writes. Inspected
crop/tree/replanting/sensor/GIS stores already own connection transactions;
single-row CRUD/settings actions remain independent, and report/projection reads
are read-only. Optional year-context audit/session bookkeeping is not certified
as an atomic business pair here; its persistence/in-memory semantics were left
unchanged. Attachment import/delete/ownership remains B3, not covered by SQL
atomicity. This checkpoint does not claim new cross-process concurrency guarantees.

Pre-fix replay against committed baseline source (loaded in memory, no checkout):
**20 cases, 17 expected failures / 3 passes / 0 errors**. Persistent partial state
was exposed for sale/activity/protection create/edit/delete; receipt/service
create/edit; both invoice posting types; sale third-write and Python-sync failure.
First-write rejection and receipt/service deletes already passed. Fixtures prime
existing lazy year-lock schema before snapshots so initialization is not mistaken
for a business mutation.

New `tests.test_transaction_integrity`: **28/28 PASS**, including whole-DB dumps
through reopened independent connections, stock/linked-state checks, first/later
SQL failures, Python/BaseException rollback, retry, one-commit trace, closed
handles and independent execute behavior. Final run starts with an English
controller, uses scoped Greek form setup and confirms that controller is restored.
**0 ResourceWarnings**; no real profiles/data or generated artifacts used.

Existing focused verification: **96/96 PASS**, for **124 distinct tests PASS**
including the new module; zero failures/errors and zero ResourceWarnings in all
three final runs. Python 3.14, `-B -X utf8`, Qt offscreen, temporary
`MASTIXA_DATA_HOME` set before imports, `unittest` loader/runner and explicit
ResourceWarning collection plus `gc.collect()`:

| `tests.` module / selected method | PASS |
|---|---:|
| `test_transaction_integrity` | 28 |
| `test_inventory_ledger_contract` | 7 |
| `test_inventory_expense_atomicity` | 5 |
| `test_inventory_quality_gate` | 3 |
| `test_equipment_maintenance_atomicity` | 4 |
| `test_equipment_maintenance_contract` | 1 |
| `test_phase16e_cross_module_validation` | 2 |
| `test_activity_projection` | 34 |
| `test_report_consistency` | 1 |
| `test_alpha2_step3_year_context` | 12 |
| `test_phase16f_realistic_performance` | 1 |
| `test_phase16i_security.ProfileArchiveSecurityTests.test_nested_manifest_and_corrupt_database_cleanup` | 1 |
| `test_stabilization` (includes all 13 HIGH #1 cases) | 23 |
| `test_phase16j_composed_ui_localization.ComposedUiTests.test_sales_insufficient_stock_product_and_no_write` | 1 |
| `test_phase16j_composed_ui_localization.ComposedUiTests.test_all_locked_headings_and_edit_state` | 1 |

The 71-test existing-contract group and 25-test stabilization/localization group
ran in separate processes. The latter completed in 380.318s; no test-harness or
production localization change was needed. Source review checked all 11 converted
entry points and shared synchronizers for independent connections/commits.
`git diff --check` PASS. No broad Database regression required a full desktop run;
Android was neither changed nor run. No schema/migration, attachment, licensing,
dependency or HIGH #1 implementation changes. B3 remains unresolved. No commit/push.

### B3 — HIGH: copied Windows profiles share destructible attachment storage

Owners: `invoice_documents.py:38`, `:388`, `:569`; `profile_manager.py:288`, `:343`.
Windows uses global `BASE_DIR/data/invoice_documents`, while profile export copies
DB metadata without attachment bytes or remapping `stored_filename`.
Android `DocumentStore` stores bytes/hash in the profile DB, and `LocalBackup`
includes those columns. Profile isolation is a shared supported requirement.

Synthetic reproduction:

1. In a temporary application root, create one invoice and dummy PDF file.
2. Export default profile using real `ProfileManager.export_profile`; archive
   members are **`manifest.json`, `profile.db`** (no avatar in this fixture).
3. Import that archive as a new profile using `import_profile`.
4. Open `InvoiceDocumentsPage` against the imported DB, confirm `delete_document`.
5. Original profile still has **1 document row**, imported profile has **0**, but
   the **original attachment file no longer exists**.

This is proven cross-profile data loss, not merely a UI or file-format difference.
Current profile tests cover registry/DB isolation and export failures, not shared
attachment ownership. Android `DocumentTest` covers attachment backup and deletion.

Required repair: define profile-owned attachment paths and archive copying/remapping,
with safe legacy resolution and shared-reference handling before deleting files.
Test same-install clone, fresh-root restore and failed import without damaging
either profile. A one-line path change would strand existing attachments and was
therefore not applied. No real attachment was read or removed.

#### B3 follow-up — 2026-09-29 (DESKTOP)

**HIGH #3: FIXED / pending final parity rerun.** Approved clean baseline
`4efac37247822a2eb0b538f984ee49c0a221625f`, branch `icon-runtime-qa-final`.
Pre-fix synthetic reproductions confirmed BOTH deletion directions: A/B resolved
the same global path; deleting either removed the other's file while retaining
the other's DB row. Export contained only manifest/database. Zero ResourceWarnings.

Ownership now follows the page's database path, not mutable active-profile state:
`<database parent>/<database filename>.attachments/invoice_documents/<stored_filename>`.
Thus default profile uses `BASE_DIR/data/mastixa_manager.db.attachments/invoice_documents`,
and generated profiles use `BASE_DIR/data/profiles/<id>/mastixa_manager.db.attachments/invoice_documents`.
Stored filenames/record IDs/schema remain unchanged. New imports write directly
to owned storage. Reads prefer owned bytes, then safe legacy
`BASE_DIR/data/invoice_documents` bytes. Legacy materialization happens by COPY
during profile import; no bulk migration/move or legacy deletion occurs.
Document delete targets only the validated owned path and retains its file while
another same-profile row references that filename (case-insensitive). Path/name
checks reject traversal, separators, ADS/device names and redirected paths.
Managed extensions match existing invoice intake: PDF/JPG/JPEG/PNG/BMP/TIF/TIFF/WEBP.

Owner-approved archive compatibility: package format **2**, SQLite schema unchanged.
V2 exports include the DB snapshot, existing metadata/avatar, and only unique
referenced attachments, resolved from owned storage or safe legacy fallback.
Missing bytes fail export and preserve any existing destination. V2 import
requires an exact match between validated DB references and attachment members;
missing or extra files fail. V1 without references still imports; V1 with references
copies ONLY matching safe legacy-global files, rejecting missing bytes even if
another profile has an owned copy. All copies enter the new UUID profile directory
before registry publication. Extraction, validation and registration-preparation
failures clean staged profile/avatar files; destination collisions never delete an
existing profile. Older releases are not required to read V2 (explicitly approved).

Strict ZIP layout: `manifest.json`, `profile.db`, at most one existing supported
`avatar.<extension>`, and `invoice_documents/<single safe managed filename>`.
Security retains Store/Deflate-only, encryption/special-file rejection, duplicate
and case-conflict rejection, SQLite integrity checks and bounded streamed copies.
Existing limits retained: DB **2 GiB**, avatar **20 MiB**, manifest **64 KiB**, total
uncompressed **2 GiB + 20 MiB + 64 KiB**, physical archive total + **1 MiB**,
compression ratio **1000:1** for members above **1 MiB**. Invoice imports previously
had no size policy: profile packages now use the existing avatar-sized **20 MiB**
per-attachment bound, **256 MiB** attachment sub-total, **1024** attachments
(at most **1027** members). These finite sub-budgets do not enlarge the existing
overall budget. Oversized existing documents produce a clear package error;
ordinary invoice intake is unchanged. Reduced-limit tests exercise boundaries.

Other consumers: document ZIP and portable data ZIP now resolve owned/fallback
files; the latter excludes duplicate references. Ordinary SQLite backups remain
DB-only; restoring in place retains owned files, but cannot restore deleted bytes
or provide a standalone attachment backup. Use profile V2 export/import for that.
Profile removal retains its existing recoverable archive behavior: moving the
profile directory to `profile_trash` carries owned attachments with it. Legacy
global storage is never removed. Default-profile removal remains prohibited.

Focused verification uses Python 3.14 `-B -X utf8`, Qt offscreen and temporary
`MASTIXA_DATA_HOME`, with ResourceWarnings visible/collected and forced GC:

| `tests.` module / selection | PASS |
|---|---:|
| `test_invoice_profile_ownership` | 34 |
| `test_profiles` | 5 |
| `test_phase16i_security` | 10 |
| `test_transaction_integrity` (all HIGH #2 cases, including both invoice postings) | 28 |
| `test_phase16d_backup_restore` | 7 |
| `test_alpha2_step5_ui.Alpha2Step5UiTests.test_invoice_documents_page_hides_all_unfinished_actions` | 1 |
| `test_profile_switch_ui` | 3 |

**88 distinct focused tests PASS; zero failures/errors and zero ResourceWarnings.**
The final 51-test ownership/profile/security/invoice-transaction rerun covers the
import-collision guard and strict filenames; unchanged remaining transaction,
backup and UI results are retained. Initial new-test
path-separator assertion was corrected to compare resolved paths; no production
failure was hidden. Existing backup failure-injection tests log expected errors.
`git diff --check` PASS. No full desktop, Android, packaged/manual GUI, external
viewer/OCR or concurrent filesystem-adversary certification is claimed. HIGH #1,
HIGH #2 transaction API/posting, licensing and original dirty checkout unchanged.
No commit/push; final parity rerun is the next phase, not performed here.

## Other differences, incomplete evidence and release risks

- **U1 — UNVERIFIED backup risk / future adapter boundary:**
  `ActivityIdentityRegistry.create` defines `activity_sync_fields` and
  `activity_sync_sources`; `LocalBackup.TABLES` includes neither and restore touches
  only listed tables. Windows whole-DB backup includes such tables automatically.
  Therefore Android metadata is omitted if populated; existing mappings can remain
  outside a restore. Registration call-site search in production found definitions
  only, so this is not presented as a newly reproduced user-facing Android data-loss
  bug. Before enabling adapters, reproduce populated-registry backup/restore and
  decide backward-compatible replacement/clearing semantics. Do not silently invent
  a new schema/version or erase mappings as an audit "fix".
- **U2 — UNVERIFIED v1.0 scope decision:** Windows Alpha2 recurrence fields
  `within_period_unit`, `within_period_interval`, `every_years`, `base_year`,
  `crop_program_field_links` and temporary year correction exceed Android's current
  Rule/Store model. The common Phase12 fixed/daily contract is tested, but that does
  not establish advanced schedule parity. These are currently Windows-only
  implementations; intentional exclusion from v1.0 must be explicit rather than
  inferred from missing Android code. Do not coerce advanced rules into `everyDays`.
- **U3 — backup capability difference:** Windows SQLite backup remains DB-only;
  B3 profile archive V2 now carries referenced invoice bytes, with fresh-root
  round-trip coverage. Android logical backups carry document bytes. Verify the
  distinct user-facing backup expectations in the final parity rerun. No
  cross-platform binary backup compatibility is asserted.
- **Intentional platform differences:** registry/auth/session implementation;
  local ID and soft-deletion representation; combined Android money table;
  imported Windows history restricted on Android; platform document pickers;
  Windows optional OCR installation versus Android offline engine; distinct backup
  containers and storage limits; report layout/export implementation.
- **Windows-only / explicit Android gating:** Shapefile/DXF conversion belongs to
  Desktop. Android `MainActivity.implemented` does not enable every `PageCatalog`
  label: declaration/package preview, generic search/data-quality/audit/export,
  online backup and general PC sync entries are not proof of supported workflows.
  They show under-construction state. No hidden successful implementation is assumed.
- **Android-only:** device/foreground GNSS capture and profile-routed background
  task reminders. Windows viewing/importing stored tracks is a separate supported
  workflow. Delivery depends on permissions and OS lifecycle.
- **Future/gated:** business sync adapters, online backup and generalized remote
  delivery. Local package preview does not send data. Current pending-change rows
  do not prove a configured network synchronization feature.
- **External/device-limited:** physical GNSS accuracy/power, provider credentials,
  licensed offline maps, official Cadastre schema/service and configured Supabase
  account/dataset/RLS. No live-service or device PASS was inferred.
- **Additional unverified limits:** full old-schema/failure matrix on Android;
  direct-SQL/multiple-process year enforcement on Windows; all supported CRS
  transforms; report numeric edge cases and cross-runtime rounding; arbitrary
  third-party SAF providers; interruption during rollback itself. Existing tests
  reduce risk but do not establish universal parity.
- Phase16I licensing/distribution remains independently **PARTIAL / owner-deferred**.
  No license, notices, Qt VirtualKeyboard or policy decisions were made here.

## Tests and execution actually performed

The results below were obtained during the 2026-09-28 audit and retained at the
2026-09-29 documentation closure. No tests or reproduction probes were rerun during
closure; current supporting source was inspected only to validate the recorded findings.

No full suite, release build, localization rerun, Android install, emulator launch,
remote service test or CI rerun was performed.

Python executable:
`<USER_HOME>\AppData\Local\Programs\Python\Python314\python.exe`.
Execution command was `python.exe -B -X utf8 -` (PowerShell here-string stdin),
with `QT_QPA_PLATFORM=offscreen`. The focused runner below is the executed Python:

```python
import os, tempfile, unittest, gc, warnings
with tempfile.TemporaryDirectory() as folder:
    os.environ['MASTIXA_DATA_HOME'] = folder
    modules = [
        'tests.test_activity_identity_cross_client',
        'tests.test_inventory_provenance_cross_client',
        'tests.test_crop_program',
        'tests.test_task_calendar',
        'tests.test_plant_tracking',
        'tests.test_sensor_data',
        'tests.test_phase16f_realistic_performance',
        'tests.test_phase16i_security.ProfileArchiveSecurityTests.test_nested_manifest_and_corrupt_database_cleanup',
    ]
    with warnings.catch_warnings(record=True) as seen:
        warnings.simplefilter('always', ResourceWarning)
        suite = unittest.defaultTestLoader.loadTestsFromNames(modules)
        result = unittest.TextTestRunner(verbosity=2).run(suite)
        gc.collect()
        resource = [str(w.message) for w in seen
                    if issubclass(w.category, ResourceWarning)]
        print('RESOURCE_WARNINGS=' + str(len(resource)))
        print('SQLITE_RESOURCE_WARNINGS=' + str(sum('sqlite3.Connection' in w for w in resource)))
        for w in resource:
            print(w)
    raise SystemExit(0 if result.wasSuccessful() and not resource else 1)
```

Result: **17 tests PASS, 0 failures/errors/skips, 0.980s;
ResourceWarnings 0, SQLite ResourceWarnings 0**, including explicit GC.
Counts by module: 1 + 2 + 4 + 2 + 3 + 3 + 1 + 1.

Two additional `python.exe -B -X utf8 -` synthetic reproduction probes executed
the real Desktop page/profile methods described in B1-B3. Both exited 0 and
printed the defect-state counts above. These were **successful reproductions of
bugs**, not passing regressions or fixes. Their source records used a fresh
field/product/buyer, 20 units harvest, sale of 5 at 10/unit, then a 4-unit harvest
edit; consumption cases used 10 receipt units and 2 consumed units. Injected
SQLite triggers used `RAISE(ABORT,'synthetic failure')` on income or source-owned
inventory insertion. Dialog confirmation was stubbed only for synthetic deletes;
unexpected warnings raised instead of opening a modal.

## SQLite ResourceWarning issue housekeeping

`git show 88c22ff` confirms explicit `closing(sqlite3.connect(...))` fixes in
the CSV, backup, performance and stabilization fixtures. Current `Database.connect`
uses `_ClosingConnection`, whose `__exit__` commits/rolls back then closes in
`finally`. The two formerly reported performance/security paths were rerun above
with warnings visible and garbage collection: zero ResourceWarnings.

The cited connection-cleanup item is **technically resolved by current test-fixture
behavior; no warning was reproduced in the focused audit**. This is not a new
zero-warning certification of the entire desktop suite. The GitHub issue was not
changed or closed. The master ledger's historical "13 warnings deferred" note is
superseded by its new current checkpoint; the historical text is preserved.

## Closure and next actions

**PARTIAL — do not declare pre-v1.0 supported-workflow parity complete.**

The first audit's research and documentation review are complete. Parity readiness
remains PARTIAL because B1/B2/B3 await the final parity rerun; public-release readiness and
Phase16I licensing closure are not claimed.

The original documentation-closure phase updated only the checkpoint and roadmap:
the confirmed failures cross transaction or file-ownership boundaries, and a broad
DB wrapper change or guessed attachment migration is not a safe minimal audit edit.

Owner-approved next-action order (supersedes the initial audit's recommendation):

1. Close/checkpoint this first Windows / Android parity audit (documentation done;
   uncommitted, no push).
2. HIGH Fix #1 — Production ↔ Sales invariant (B1): FIXED / pending final parity rerun.
3. HIGH Fix #2 — atomic linked writes / transaction integrity (B2): FIXED / pending final parity rerun.
4. HIGH Fix #3 — profile-owned invoice attachments (B3): FIXED / pending final parity rerun.
5. **Next: rerun the Windows / Android parity audit**, including U1/U2/U3 and appropriate
   Android runtime evidence; preserve explicit external/device limitations.
6. Deep Cross-Feature Real-World Usage Audit: mandatory before v1.0; target at
   least 60–100+ realistic scenario journeys where practical. Scope and execution
   ownership are recorded in [MASTER_PROGRESS.md](MASTER_PROGRESS.md).
7. Final pre-v1.0 verification / release gate. Distribution/licensing remains a
   separate owner-deferred track and is not implicitly cleared by technical gates.

No fix, deep-audit implementation or next phase was started during the original closure.

Original closure validation: `git diff --check` plus `git diff --no-index --check -- NUL
docs/PRE_V1_WINDOWS_ANDROID_PARITY.md` passed. Only this new document and
`docs/MASTER_PROGRESS.md` are changed;
production/tests/dependencies are unchanged, original checkout untouched,
`diagnostics/` absent. No commit or push.
