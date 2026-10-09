# Windows source blocker closure from the public repository

The active development baseline is
[`d98f041d3f7769548d22a8892c257aa7883b2a02`](https://github.com/Sxara242/Mastixa-Manager-Source/commit/d98f041d3f7769548d22a8892c257aa7883b2a02).
All changes below are developed in the public checkout; private archives remain
untouched. Windows rc.2 is still unbuilt and unqualified. Android remains in development.

The initial publication audit passed. The initial Windows baseline was 123/133
modules passing, nine failing and one timed out. This page distinguishes source
defects from stale fixture contracts; no failing test is skipped or marked xfail.

| Initial module | Classification | Diagnosis and correction |
| --- | --- | --- |
| test_batch5_ui | A: application regression | Physical-lock reads created year_locks during rejected form validation. Initialize the table with the normal DB schema and make lock reads pure, including legacy missing-table databases. A new test verifies no writes/schema changes. |
| test_money_sort_localization | C: test-harness defect | Fixture rows were dated 2027 but current working-year defaults selected another year. Set the fixture's working year explicitly; preserve every sort/data/read-only assertion. |
| test_owner_ui_acceptance | C: staged UI fixture defect | The constrained-window test accessed finance_table before below-fold staged construction. Complete it with the existing deliberate-scroll hook before inspecting tables. |
| test_phase16j_accessibility_focus | C: obsolete theme contract | The theme now installs both scoped skins once. Assert active root properties, dark focus selector scoping, ring colors/uniqueness and no repeated global stylesheet replacement. |
| test_phase16j_annual_localization | C: fixture initialization defect | Captured read-only baseline before initializing working-year preferences. Initialize 2026 first; retain exact numeric/export/database equality assertions. |
| test_phase16j_coordinate_ui | B: localization regression | Selection/error refresh wrote raw Greek after English translation. Render dynamic notes through the current translator; preserve raw parcel values/file formats. |
| test_phase16j_file_dialog_localization | C: stale export mock | Export consumes an immutable AnnualSnapshot; the mock only provided the former year selector. Provide snapshot.year=2027 and retain exact filenames/cancellation checks. |
| test_phase16j_generated_tables_localization | C: year fixture defect | Synthetic 2027 rows were filtered by default working year; crop test snapshots preceded year initialization. Set explicit matching contexts before snapshots; retain canonical search/body/identity/database assertions. |
| test_phase16j_static_selectors_localization | C: year fixture defect | Service records dated 2027 were filtered out. Set fixture working year 2027; preserve real upcoming/overdue/date calculations and selector assertions. |
| test_stabilization | C/E: Qt fixture lifecycle and process budget | Whole-window fixture left application-owned theme/language filters alive across tests. Delete owned controllers/widgets, restore prior language/style/palette before deleting DBs. All 23 assertions completed in a measured 284-second diagnostic; use an explicit 360-second module bound, with stack diagnostics and unsuccessful process exit still failing. Final complete verification pending. |

No suite-order/inter-module contamination (D) is asserted without evidence.
The runner isolates modules and executes unittest classes plus plain functions.
The normal bound remains 120 seconds, with only the measured stabilization
override visible in the CI command. A timeout still fails and kills only the
owned test process tree. No blanket timeout waiver is introduced.

The completed baseline hosted Windows run reported 119/133 passing modules,
ten failed modules and four timeouts (888 completed cases). In addition to the
local baseline, it found appearance-persistence fixture comparisons between
Windows 8.3 temporary-directory aliases and their canonical long paths (C).
Resolve the fixture root before retaining the exact path equality assertions.
Three additional modules made assertion progress until the hosted 120-second
bound: activity-expense sync (20 cases, 67 seconds locally), composed localization
(33 cases, 21 seconds locally), and sale sources (29 cases, 58 seconds locally).
These are E: hosted runtime-budget findings pending complete bounded confirmation.
Use explicit 240/180/360-second hosted bounds respectively; all assertions and
unsuccessful-exit/timeout handling remain required. Stack diagnostics distinguish
any remaining blocked call from slow progress. The default remains 120 seconds
for other modules. Final hosted source clearance requires every module to pass.

All nine originally failing modules pass focused local checks after correction.
Focused year-context/owner-fix/transaction checks also pass. Complete local
validation passes: 133 modules, 994 cases, zero failures/timeouts. The subsequent
hosted path-fixture delta passes all ten appearance tests locally. Hosted validation
of the corrected tree is pending; this is not rc.2 build clearance.

The first hosted run actually started Windows on windows-latest and source audit/
Android on ubuntu-latest:
[run 37970053180](https://github.com/Sxara242/Mastixa-Manager-Source/actions/runs/37970053180).
Source audit passed. Android SDK setup failed before build because its action
requested the retired tools package. Workflows now request platform-tools
explicitly (plus emulator for manual instrumentation), as supported by
[the action's package input](https://github.com/android-actions/setup-android#additional-packages).
That correction passed SDK setup in hosted run 37972481782. The next failure
revealed Windows CRLF in the Unix Gradle launcher; normalize android/gradlew
to LF and enforce that checkout format through .gitattributes. This changes
launcher line endings only and preserves the wrapper JAR/distribution locks
and all third-party license texts. A fresh hosted build/lint must validate it.
Packaging/legal preflight runs even when source tests fail; normal CI still builds
no installers and uploads no artifacts. One-day optional QA retention is unchanged.

The central year_locks schema is already part of the desktop/Android exchange
contract; this change moves creation to database initialization and does not
relicense third-party code or change qualified shipping dependencies. Complete
Windows parity/schema checks remain in the full suite; Android build/lint remains
development validation. Frozen rc.2, installation and owner acceptance are separate gates.
