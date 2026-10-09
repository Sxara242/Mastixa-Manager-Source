> Retained historical engineering record, sanitized for public review.
> Current status: [RELEASE_STATUS.md](RELEASE_STATUS.md). This record does not
> establish approval of the current source or a new binary release. Local-only
> receipt paths refer to privately retained evidence, absent from this snapshot.

# Master execution ledger

## Android parity planning — accepted Windows v1 scope

**SHARED documentation-only planning.** The owner accepts Windows v1 proceeding
without exact Android feature parity. U2 Windows-only capabilities do not block
Windows v1; Android should later reach functional parity in business rules,
supported workflows and data contracts, with platform-specific UI/implementation.
The [U2 TODO plan](PRE_V1_WINDOWS_ANDROID_PARITY.md#android-u2-todo-plan--accepted-scope-checkpoint)
records weekly/monthly/once recurrence, multi-year/base-year rules, persistent
program-field links, active-year context, temporary correction and the documented
profile date-display preference difference. Proposed future batches A1–A5 include
current behavior/status, targets and shared-data implications for each item.
No implementation or test run in this planning checkpoint; Android connected-device
validation remains pending. This supersedes earlier requests for a U2 scope decision,
without changing U1/U3 or authorizing the next implementation/audit phase.

## Final Windows / Android parity rerun — 2026-09-29

**SHARED verification: SUPPORTED-WORKFLOW PARITY VERIFIED FOR THIS CHECKPOINT.**
Baseline `8a06f95ae8e0604779dd47c47f4e52f5708db3da`, branch
`icon-runtime-qa-final`. This supersedes the pending-rerun status below.
**B1/B2/B3 VERIFIED FIXED** through source/contract comparison and Windows tests;
no new material parity defect demonstrated. No production/test changes needed.

Recovered completed execution: **683/683 desktop discovery PASS**, **213/213
focused PASS** (including all 13 B1 cases, 28 transaction and 34 attachment cases),
and **3/3 isolated profile-switch PASS**. Zero failures/errors/skips or
ResourceWarnings; overlapping counts are not additional distinct tests. The delayed
profile-switch case completed in every run; no harness change was required.
Android `testDebugUnitTest lintDebug assembleDebug assembleChecksAndroidTest`:
BUILD SUCCESSFUL, lint 0 errors / 11 warnings. JVM task NO-SOURCE; instrumentation
compiled only. **No connected device: Android runtime validation remains pending.**

**U1 deferred:** activity-identity backup tables need policy/coverage before business
adapter activation. **U2 scope accepted:** advanced Windows-only recurrence,
field links and year-correction capabilities do not block Windows v1; future
Android parity work is recorded in the TODO plan above. **U3 documented:** Windows SQLite backup excludes attachment bytes;
V2 profile export includes referenced bytes. These qualifications prevent an
unconditional all-platform/runtime or public-release claim. See
[complete parity evidence and exact test inventory](PRE_V1_WINDOWS_ANDROID_PARITY.md).

**Next: DEEP CROSS-FEATURE REAL-WORLD USAGE AUDIT**, then final pre-v1 verification /
release gate; neither started here. Phase16I remains PARTIAL / owner-deferred.
Documentation-only checkpoint; original dirty checkout untouched, diagnostics
absent, no generated artifacts included, no commit/push.

## HIGH Fix #3 checkpoint — 2026-09-29

**DESKTOP: profile-owned invoice attachments FIXED / pending final parity rerun.**
Approved baseline `4efac37247822a2eb0b538f984ee49c0a221625f`; branch
`icon-runtime-qa-final`. This supersedes the historical HIGH #2 next-action below.
Attachment ownership follows the database-specific `.db.attachments/invoice_documents`
directory. Legacy global bytes are read/copy-only; deletion preserves other profiles
and same-profile duplicate references. Profile removal retains recoverable files.

Owner-approved profile-package V2 includes every referenced managed attachment;
missing bytes fail clearly. V1 imports remain supported: referenced files must be
recoverable from safe legacy global storage and are copied into the new profile,
otherwise import fails with cleanup before registry publication. Archive security
retains existing bounds with finite attachment sub-limits. No SQLite schema change.
SQLite backups remain DB-only; portable profile V2 packages carry attachment bytes.

**88 distinct focused tests PASS, 0 failures/errors, 0 ResourceWarnings**: ownership
34, profile 5, Phase16I security 10, HIGH #2 transactions 28, backup 7, invoice UI 1,
profile-switch UI 3. `git diff --check` PASS. See [B3 evidence](PRE_V1_WINDOWS_ANDROID_PARITY.md)
for exact paths, limits, compatibility policy, tests and limitations. No production
HIGH #1/#2, Android, migration, licensing or dependency changes; original dirty
checkout untouched, diagnostics absent, no generated artifacts or commit/push.

**All three confirmed HIGH defects are fixed; overall parity remains PARTIAL.**
**Next: Windows ↔ Android parity rerun**, then the mandatory Deep Cross-Feature
Real-World Usage Audit, then final pre-v1.0 verification/release gate. None starts here.

## HIGH Fix #2 checkpoint — 2026-09-29

**DESKTOP: atomic linked writes FIXED / pending final parity rerun.** This entry
supersedes the next-action pointer in the historical HIGH #1 entry below.
Baseline `4c05d6fd4671853ec86d3584821153357e278e4b`; branch `icon-runtime-qa-final`.
An explicit one-connection transaction now covers sale/income, activity/consumption,
protection/consumption, receipt/expense, service/expense/meter and invoice financial
posting. Commit once on success; rollback and close on failure. Existing standalone
execute, SQLite settings, validations and canonical values remain unchanged.

Pre-fix baseline replay: **17 expected failures / 3 passes**. Final verification:
**28 atomicity + 71 existing-contract + 25 stabilization/localization = 124 PASS**,
zero failures/errors, **0 ResourceWarnings**. The 25 include all **13 HIGH #1**
invariant cases. Reopened whole-DB snapshots, retry and connection cleanup are
covered; scoped language fixtures restore a pre-existing English controller.
Full desktop/Android runs were not needed; `git diff --check` PASS. See the
[B2 evidence and exact focused test list](PRE_V1_WINDOWS_ANDROID_PARITY.md).

**Next: HIGH Fix #3 — profile-owned invoice attachments.** B3 remains unresolved;
B1/B2 await the final parity rerun, so overall parity stays **PARTIAL**. No
attachment, Android, schema/migration, dependency or licensing changes; no
diagnostics/generated artifacts, commit or push. Original dirty checkout untouched.

## HIGH Fix #1 checkpoint — 2026-09-29

**DESKTOP: Production ↔ Sales invariant FIXED / pending final parity rerun.**
Baseline `a51b01717842d7f6215df2cb332598ab718a85a0`; branch `icon-runtime-qa-final`.
Read-only hypothetical stock checks now reject production edits/deletes that leave
either affected product below existing sales, using SalesPage's `0.000001`
tolerance. Product-level totals, legacy links, inactive history, year locks and
create behavior are preserved. Rejections leave whole-DB snapshots unchanged and
use protected EL/EN warning templates. See the [B1 evidence](PRE_V1_WINDOWS_ANDROID_PARITY.md).

Closure verification: retained **23/23 stabilization PASS**, including **13/13 new
invariant cases**; fresh **15/15 year-context/composed-localization PASS**, plus
**2/2 active-English-controller repeats**. An unrelated existing modal-mock gap
required only scoped `QMessageBox.exec` interception in two year-context tests;
production year behavior and assertions remain unchanged. `git diff --check` PASS.

**Next: HIGH Fix #2 — atomic linked writes / transaction integrity.** B2 and B3
(profile-owned invoice attachments) remain unresolved; overall parity is PARTIAL.
No transaction redesign, attachment fix, Android/schema/migration/licensing work,
commit or push in this task. The original dirty checkout remains untouched.
The ordered parity rerun, mandatory deep cross-feature audit and final gates below
remain required; none starts here.

## Current pre-v1.0 parity checkpoint — 2026-09-29

**SHARED (DESKTOP + ANDROID), documentation-only closure.** This entry supersedes
older current/next-action notes below; historical evidence is preserved.
Baseline: `762223f3693ca63146d2c869f776c5bf8d09e24f` (`Add packaged Windows startup
smoke test`), branch `icon-runtime-qa-final`, approved `Mastixa-Icon-Diagnosis`
worktree. The original dirty `MastixaManager` checkout remains untouched.

The first [Windows / Android parity audit](PRE_V1_WINDOWS_ANDROID_PARITY.md) is
**research-complete / formally closed as an audit checkpoint**. **Parity readiness
remains PARTIAL**: three reproduced HIGH defects remain unresolved: Windows
production edits/deletes can leave sold quantity above produced quantity; linked
sale/income and activity/protection/inventory writes can commit partially; copied
profiles can share an invoice attachment that deletion in one profile removes
from the other. No production/test changes or fixes were made in this closure.

Retained audit evidence: **17 focused tests PASS; 0 SQLite ResourceWarnings**.
The connection-cleanup issue is technically resolved by current test-fixture
behavior with no warning reproduced in that focused run; the GitHub issue remains
untouched. This supersedes the old deferred-warning note, not a fresh full-suite
certification. Normal Android CI compiles instrumentation tests but does not run
them; no device was connected during the audit. Android source/regression coverage
is not fresh Android runtime PASS. No live Supabase or physical GNSS verification.
No tests/CI/builds were repeated for this documentation-only closure.

### Required next-action order

1. Close/checkpoint the first Windows ↔ Android parity audit — documentation
   reviewed; changes remain uncommitted, no push.
2. HIGH Fix #1 — Production ↔ Sales invariant: FIXED / pending final parity rerun.
3. HIGH Fix #2 — atomic linked writes / transaction integrity: FIXED / pending final parity rerun.
4. HIGH Fix #3 — profile-owned invoice attachments: FIXED / pending final parity rerun.
5. **Next: Windows ↔ Android parity rerun**, including the recorded residual risks.
6. **Deep Cross-Feature Real-World Usage Audit — mandatory before v1.0.**
7. Final pre-v1.0 verification / release gate.

Phase16I distribution/licensing remains intentionally PARTIAL and owner-deferred,
with independent public-release blockers. No licensing closure or public-release
readiness is implied by this sequence. None of the next phases starts here.

### Mandatory deep cross-feature audit (planned, not started)

Use many realistic human-use journeys, targeting **at least 60–100+ scenarios
where practical**, not only isolated module tests. Include these combinations:

- Create → edit → edit again → delete → recreate; parent → linked child → edit
  parent → verify child/invariant; deleting parents with dependent records.
- Production → sale → income → edit production → edit sale → delete → year lock.
- Inventory receipt → expense → farm consumption → correction → delete source.
- Field → product → production → activity → protection → reports.
- Crop program → generated tasks → calendar → notifications → completion/edit.
- Planting → tree tracking → loss/replanting → timeline.
- Invoice attachment → profile export → profile import → edit/delete in one profile.
- Backup → multi-module changes → restore → verify all relations; duplicate imports
  and stale references; restart between steps and profile switching between workflows.
- Localization switching with existing canonical values; year-boundary edits and
  year locks; partial failure during multi-write operations and rollback verification.
- Reports/derived totals after edits/deletes; supported Windows → Android → Windows
  round trips only (unsupported transfer directions remain explicit).
- GIS geometry → points/tracks → CRS export/import → identity/sync projections.
- User mistakes (wrong product/date/quantity) followed by correction; repeated
  actions and double-submit-like behavior where applicable.

For applicable scenarios verify user-visible results, database state, linked
records, derived totals, file ownership, profile isolation, edit/delete lifecycle,
restart persistence, backup/restore persistence and rollback after injected failure.
Use isolated synthetic data; unsupported or external behavior must not become PASS.

Owner-decided execution model: **ChatGPT designs the large scenario matrix/audit
plan; Codex HIGH implements automated integration/regression tests and justified
fixes; manual/device testing covers true GUI/device/GNSS/external behavior that
automation cannot prove.** This checkpoint records the requirement only.

## Active release checkpoint — 2026-09-21

**DESKTOP + RELEASE-INFRA: packaged theme persistence and Dark dashboard
contrast are CLOSED / VERIFIED FIXED.** This checkpoint supersedes older
current/next-action notes below. Stable execution rules are in `AGENTS.md`.

- Worktree: `<WORKSPACE>\Mastixa-Icon-Diagnosis`.
- Local branch: `icon-runtime-qa-final`; push target: `hotfix/0.40.0-alpha.2-ui`.
- Tested source baseline: `ffa0692dfc1b0e9a02018663ca62a11fc8e12459`, plus the
  runtime fixes recorded with this checkpoint. Icon work remains CLOSED.
- The original dirty `MastixaManager` checkout on `refactor/pages`, its PNG
  modifications and backup folder remain untouched. No Android/icon changes.

### Runtime defects and fixes

The workflow #64 Sandbox smoke found two defects: Dark was lost after
KEEP DATA uninstall/reinstall, and dashboard KPI values had low Dark contrast.

- Theme storage moved from the installed
  `%LOCALAPPDATA%\Programs\Mastixa Manager\_internal\data\appearance.ini`
  to canonical `runtime_paths.BASE_DIR / data / appearance.ini`, normally
  `%LOCALAPPDATA%\MastixaManager\data\appearance.ini` in frozen Windows runs.
  Existing new settings win. A valid legacy light/dark preference migrates when
  the new file is absent; failed writes fall back non-fatally for that run.
  The legacy file remains untouched. Existing KEEP DATA/full-purge semantics
  cover the new path without installer changes.
- Dark styling now uses `DashboardPage QLabel#metricValue` with `#E7ECEF`.
  Contrast is approximately 12.71:1; unrelated metrics and Light colors remain
  unchanged. Production change: `app/appearance_theme.py`; regression coverage:
  `tests/test_appearance_persistence.py`, `tests/test_dashboard_theme_contrast.py`.

### Verification and owner acceptance

- Final focused tests: **31 PASS**, zero failures/errors.
- Fresh full desktop suite on final code: **425 PASS**, zero failures/errors.
- `git diff --check`: **PASS**. Source/test hashes matched the verified files
  during recovery; these completed tests/builds were not rerun.
- PyInstaller bundle built successfully. Owner manually completed Inno build.
- NEW runtimefix installer SHA-256 (owner supplied):
  `94D665EE38050EFD1CA920C53396878DDFD9C457B15F69866F8F5249DC3C8AA0`.
  This is distinct from the immutable workflow #64 artifact.
- Owner manual Windows Sandbox results: **ALL PASS** — Dark KPI contrast;
  Dark and synthetic data after normal restart; uninstall KEEP DATA; reinstall;
  Dark and synthetic data after uninstall/reinstall. Both runtime defects are
  **CLOSED / VERIFIED FIXED** on this evidence. No new Codex Sandbox run.
- **13 SQLite ResourceWarnings:** non-blocking, deferred cleanup.
- **Bitdefender error 32:** local build-environment interference, as reported by
  the owner; not a runtime-fix failure. No security-setting changes in this phase.
- Tested build toolchain: Python 3.14.6, PyInstaller 6.22.2, hooks-contrib 2026.7,
  Inno Setup 6.7.3. Production pins and installer behavior remain unchanged.
- QA evidence stays outside git under
  `<WORKSPACE>\ReleaseQA_runtimefix_20260920`; original smoke
  evidence is under `ReleaseQA_ffa0692_gate64\sandbox-results`. Do not commit
  diagnostics, logs, installers or other generated QA artifacts.

### PyInstaller 6.22.3 compatibility checkpoint — VERIFIED PASS

Manual isolated QA validated the Windows packaging toolchain using:

- Python 3.14.6
- PyInstaller 6.22.3
- pyinstaller-hooks-contrib 2026.7
- Inno Setup 6.7.3

Evidence:
- packaging contract tests: **11/11 PASS**
- isolated PyInstaller bundle build: **PASS**
- bundle static verification: **PASS**
- 34 menu/icon PNGs and 13 locale files present
- no bundled application/user data directory
- only allowed dependency database: pyproj `proj.db`
- direct packaged EXE launch/navigation smoke: **PASS**
- Inno Setup QA installer build: **PASS**
- Windows Sandbox installer/launch/navigation smoke: **PASS**
- QA installer SHA-256:
  `BF9317DB3C4F40576A5F1AC0274AAC6B3E805B65E42800E5D17E241EFE39B5C7`

Production build pins are now updated together to PyInstaller 6.22.3 and
pyinstaller-hooks-contrib 2026.7. No application, Android, schema or installer
behavior change was required.

### Next checkpoint — PENDING

The 13 non-blocking SQLite ResourceWarnings remain deferred cleanup.
Phase16J localization/responsiveness/accessibility closure and the pre-v1.0
Windows↔Android parity audit remain separate later checkpoints.

Historical execution ledger for the superseded maps roadmap (phases below use
that old numbering, not the current Fieltra 16-phase roadmap). Current source,
Git/CI evidence and the feature-specific Phase 9–16 documents take precedence.
The obsolete MASTER_EXECUTION_PLAN.txt was retired on 2026-09-12 after a
repository reference scan: only this ledger referenced it; no application,
test, CI or packaging dependency was found.

## Current Fieltra checkpoint — Phase 16I (2026-09-13)

Current follow-up: **Phase16J PARTIAL**, explicitly authorized after the pushed
Phase16I documentation checkpoint `f08b123`. First scoped Windows localization
boundary fixes committed as `bec01b57f6cad19b600298fada8148e018f797ae`, with 8/8
focused checks PASS. Owner requested checkpoint-only stop at approximately 19%
usage; that historical stop was superseded by the next explicit resume request.
Windows help continuation now covers all 96 general/contextual catalog entries,
adds 18 complete English phrases and fixes HTML-escaped phrase matching. Latest
focused help result: 10/10 PASS. Coordinate export dialog localization then passed
2/2 focused UI tests plus 1/1 existing atomic failure/cancellation check, preserving
user data and file-format headers. Main parcel-map captions and summary templates
then passed 2/2 new checks: names/source filenames stay intact during language
cycles. Three further focused tests passed for nested GIS dialogs/messages
and point-type display, with data/protocol values unchanged. Other Windows UI,
Android localization, scaling and final accessibility remain. A6 then filled 35
remaining static Greek UI-source gaps; AST catalog and live text cycles passed
2/2. Latest owner instruction (~27% usage) closes only this opened block and
requests a pushed recovery checkpoint; no new subsection begins now. Application/
test HEAD `89069ff466b7f910e07ae8b7b4d583cbb89ca29f` was pushed and remote-verified
on `refactor/pages`; the documentation-only follow-up records the result. Fresh CI is deferred until Phase16J completion. See
[Phase16J resume ledger](PHASE16J_ACCESSIBILITY_LOCALIZATION.md) for completed
areas and exact next action. Phase16K not started. The Phase16I status and
public-release blockers below remain unchanged.

Pre-release audit baseline `4b63e4d`, CI #143 green, preserved. Phase16I security
review applied bounded profile archives, diagnostic exception privacy and forced
local-only PROJ transforms. Focused evidence: 23 distinct tests PASS. See
[Phase16I review](PHASE16I_SECURITY_PRIVACY.md), network and third-party inventories.
Permanent policy: NO telemetry, analytics, advertising, behavioral tracking or
automatic diagnostic uploads; local diagnostics only, future support export manual.
CI #144 (`34719309041`) is SUCCESS for Desktop and Android on pushed
`bcedfeea02bb40bfa9032427127ec1cbf1a16aaa`; confirmed read-only, not rerun.
The native/license continuation is documentation-only: inspected local wheel
contents, existing Windows bundles, cached Android inputs and current-head APK.
All 16 APK native members equal their cached AAR counterparts; no newly
demonstrated automatic upload/analytics activation. Complete binary provenance
remains UNVERIFIED, not automatically a release blocker.
Official 16I closure remains **PARTIAL** because concrete distribution gaps
remain: project-license decision, GPLv3/commercial Qt VirtualKeyboard in inspected
Windows bundles, missing complete shipped third-party notices/source provision,
and asset/platform redistribution provenance. See
[native assurance](PHASE16I_THIRD_PARTY_PRIVACY.md) and
[license decision/readiness](PHASE16I_LICENSE_READINESS.md).
No application/configuration change, test/CI/gate rerun or final LICENSE addition
in this continuation. Next step is owner's license/commercial-use policy decision
and a bounded distribution-compliance checkpoint. Phase16J not started.
Historical phase numbering below is superseded.

### Owner decision and persistent public-release blockers

**PHASE 16I STATUS = PARTIAL**

**PROJECT LICENSE DECISION = DEFERRED BY OWNER**

The owner will decide the final project/distribution license later, after learning
whether FUTO is interested in collaboration/support. This deliberate deferral is
not a technical security failure. It permits Phase16J work, not public release.
No LICENSE is selected or added and no FUTO approval is implied.

Before PUBLIC RELEASE, retain and resolve:

1. Final project/distribution license decision by the owner.
2. Qt VirtualKeyboard: inspected Windows bundles include GPLv3/commercial
   `Qt6VirtualKeyboard.dll`. Remove it from the final bundle if unused; otherwise
   establish a compatible distribution/licensing model.
3. Complete Windows and Android third-party licenses/notices.
4. Android Tesseract/Leptonica/OCR native license materials, required notices and
   applicable source-access information.
5. Rights/provenance documentation for icons, fonts, images and bundled resources.
6. Platform redistributable obligations.
7. Map every actual final Windows/APK binary/resource to known licenses and duties.
8. Preserve the partly UNVERIFIED native behavior/provenance assessment; lack of
   complete binary certification alone is not a release blocker or a PASS claim.
9. Permanent policy: telemetry, analytics, behavioral tracking, advertising and
   automatic diagnostic upload = NEVER. Diagnostics stay local; support export
   must be user-initiated/manual. Agricultural GPS tracks are user data, not
   behavioral tracking.
10. Final release verification must confirm ZIP/profile hardening, redacted
    exception logging, explicitly disabled PROJ networking and no unexpected
    background network behavior remain effective.

These items survive subsequent Phase16J/16K progress until explicitly resolved.

## Retained constraints from the retired roadmap

- Preserve user data and valid local changes; no destructive Git/history rewrites,
  committed secrets/live databases/local configuration or generated artifacts.
- Resume from status/diff/staged diff, history/tags and actual test evidence;
  distinguish complete, partial and externally blocked work. Never infer PASS
  from inspection or rerun verified work without a relevant change.
- Preserve original geometry and declared CRS alongside normalized WGS84;
  ordered parts/rings and source precision must survive export/sync. Existing
  contracts and limitations: GIS_PHASE3_STATUS.md, CRS_VERIFICATION.md,
  GIS_SYNC_VERIFICATION.md and PHASE8_NETWORK_QA.md.
- Cadastre retrieval may use only officially published documented services,
  never private map endpoints or scraping; verify actual schema/CRS before use.
  Keep file import fallback and required Cadastre attribution. Live status is
  dated evidence in GIS_PROVIDER_VERIFICATION.md, not permanent unavailability.
- Optional Google/Copernicus/offline-pack providers need official configuration
  and permitted licensing. No public OSM bulk prefetch or unauthorized imagery
  caching/digitization. Foreground GPS is not survey-grade; real GNSS accuracy,
  battery use and field conditions require physical-device verification.
- Keep polygon conflicts explicit, not silently merged. Live Supabase/RLS needs
  configured test credentials/data; never embed service-role keys in clients.
- Audit data integrity, legacy features, lifecycle/interruption, performance and
  privacy using focused reproductions and minimal fixes; avoid cosmetic redesign.
  Report severity, exact tests/results, remaining limitations and release verdict.

All other operational feature requirements/evidence are retained in the linked
GIS/QA documents and the chronological entries below; the old phase sequence is
not a second current execution plan.

Updated 2026-09-10. This ledger records evidence, not a claim of full completion.

Current position: **Phase 8 COMPLETE for configured local/emulator QA** using
retained verified results and the user's scoped final gate. Android build and
instrumentation compilation passed; lint passed with 0 errors / 12 warnings;
the two directly affected Activity lifecycle/permission regressions passed
2/2 (5.446s). No production/test source changed during that final gate.
See `PHASE8_NETWORK_QA.md` for exact commands, logs and external limitations.
No commit/tag/push was made; the Phase 8 checkpoint is ready for a separately
authorized normal source-only commit/push. Phases 9–17 remain NOT STARTED.
Chronological entries below describe the state at their respective earlier runs.

## Phase 0 — COMPLETE

Finished the pre-existing Android Dashboard/Alerts task before architecture work.
Build: `assembleDebug assembleChecks assembleChecksAndroidTest` passed.
Full isolated emulator suite: **96 tests passed, 151.285 seconds**, log
`/sdcard/mastixa-dashboard-tests.txt`. Greek/English Dashboard and alert screenshots
reviewed. Main debug APK installed with `adb install -r`: Success; WelcomeActivity
launch Status: ok. No profile data cleared. Existing desktop diff preserved.

## Phase 1 — COMPLETE: architecture assessment

- Git root is this directory, branch `refactor/pages`, HEAD `9db4e41`.
  Origin is `https://github.com/Sxara242/Mastixa-Manager.git`; existing tag
  `v0.40.0-alpha`. Android is absent from tracked files; local source is the
  sibling `../MastixaAndroid`. Remote history still needs verification in phase 2.
- Desktop: Python/PySide6, `main.py`, page modules in `app/`, SQLite profile
  databases. `Database.initialize` and per-module table initialization are the
  actual migrations; `database_infrastructure/migrations.py` is a placeholder.
  Integer desktop entity IDs, module-specific relationships, existing finance /
  stock synchronization are local transactions, not cloud synchronization.
- Android: native Java 17, AGP 8.13.2, Gradle 8.13, SDK 36/minimum 26.
  Programmatic activities and stores, per-profile SQLite schema 12, explicit
  upgrade paths and backup validation for previous versions, UUID/revision/
  tombstones and local pending changes. `.checks` isolates instrumentation data.
  Bundled offline OCR; Windows ZIP import is additive and is not bidirectional sync.
- Both clients have field name/KAEK/location text but no geometry, map renderer,
  GNSS tracking, coordinate exports or Supabase transport. Android manifest has
  no network/location permission. Existing reports export CSV/PDF/XLSX.
- Desktop tests use unittest and temporary databases / Qt offscreen; Android
  has 96 instrumentation tests. No existing GitHub workflow or lint setup found.
  Desktop packaging is PyInstaller/Inno Setup; Android wrapper is present.
- Preserve desktop layout and runtime paths. Copy curated Android source into
  `android/`, preserving the original sibling. Do not copy caches, builds, SDK,
  local.properties or user data. Shared fixtures/contracts are appropriate;
  literal Python/Java implementation sharing is not.
- Later GIS work requires additive versioned storage on both platforms,
  original geometry + declared CRS + normalized WGS84, independent provider/
  domain/persistence/export boundaries. Sync must preserve conflicting geometry.
  Existing destructive removal of obsolete connection/queue tables in desktop
  initialization must not be reused for new sync state.

## Ordered checklist / current position

- [x] 0 Finish current task and verify.
- [x] 1 Inspect architecture before major changes.
- [x] 2 Checkpoint pushed and remote content verified; hosted CI status unverified.
  Integrated Android, exclusions/secrets review, portable build, CI,
  desktop tests + Android lint/build, staged review, commit/push/tag
  `android-before-maps-qa`, verify remote/CI.
- [x] 3 Local GIS/maps/GPS/points/tracks implemented and tested; external Cadastre,
  licensed offline packs, Google/Copernicus configuration and physical GNSS field
  verification explicitly blocked/limited. See GIS_PHASE3_STATUS.md.
- [x] 4 Coordinate exports, both clients: CSV/XLSX/PDF/GeoJSON/KML, one/selected/all,
  WGS84 or actual source XY, preview, ring/part ordering and safe output handling.
- [x] 5 Coordinate transformation verification; shared published reference pairs,
  reverse tolerances and incompatible-CRS regression fixed. See CRS_VERIFICATION.md.
- [x] 6 Local sync contracts, SQLite state, conflicts and actual cross-client exchange
  verified; live Supabase account/dataset/RLS integration BLOCKED EXTERNAL.
- [x] 7 Maps checkpoint `404bd12`, tag `maps-before-full-qa`, normal push and
  independent remote-tree verification completed.
- [ ] 8 Full functional QA.
- [ ] 9 Performance audit.
- [ ] 10 Architecture/code quality audit.
- [ ] 11 Error handling.
- [ ] 12 Security/privacy.
- [ ] 13 Static analysis and critical regression tests.
- [ ] 14 Severity-based fixes.
- [ ] 15 Full retest with exact statuses.
- [ ] 16 Final checkpoint.
- [ ] 17 Factual final report.

## Resume

Read the current task and feature documentation, this historical ledger, git status/diff/cached,
history/tags and actual test reports first. Do not rerun one-use scripts under
the original Android `.tools`, reset user passwords or replace profile databases.
Phase 2 checkpoint is uploaded and verified; phase 3 is in progress.

Phase 2 local evidence: Android integrated with source-copy hash verification;
portable build configuration, root exclusions and dual-client CI added.
Windows 25/25 tests passed (228.255s). Android build/lint passed after fixing
older-API Java compatibility with desugaring and Welcome system Back handling.
Lint 0 errors/8 warnings. Full integrated instrumentation 96/96 (93.385s),
including added system Back assertion. Main APK installed, launch Status: ok.
Pre-stage source/ZIP/history scan found no credentials or forbidden files.
Staged contents inspected, ignored data/build/signing paths checked.
Local commit `9cce2b6`, tag `android-before-maps-qa` created successfully.
After the earlier approval rejection and failed misspelled destination, the user
explicitly authorized the existing working `origin`. Normal pushes of branch and
tag SUCCEEDED to `https://github.com/Sxara242/Mastixa-Manager.git`.
Remote branch and peeled tag both point to
`9cce2b61889bee39f14138482aac5ed0dc152aa0`.
Independent bare clone verified remote tree
`b8b39ac7d33d4b4a667e482ec5f8acb940b390e8`, identical to the audited local checkpoint.
212 tracked files, 90 under Android; required Windows/Android source and wrapper
present; no forbidden data/build/signing files or credential-pattern findings.
Anonymous GitHub API returned 404, so hosted Actions run status is not verified.
No new checkpoint or history rewrite; all current GIS changes remain uncommitted.

Phase 3 in progress: Python geometry normalization/validation, bounded GeoJSON/KML/
GML/Shapefile ZIP/DXF imports, additive GIS storage and native Qt map UI added.
Seven domain/import/storage tests and one offline map UI test pass. Full Windows
suite now **33 passed, 123.026 seconds**. Screenshot with synthetic parcel and
Windows Segoe UI reviewed (`.tools/parcel-map-desktop.png`). OSM visible-tile
provider code exists but live tiles not tested; offline packs explicitly blocked
without licensed provider. New Android ParcelGeometry engine using JTS/Proj4J/
GeographicLib builds and lint passes; four geometry instrumentation tests passed
(3.227s). Android GeoStore with indexed typed JSON records, migration 12→13,
backup schema 13/legacy compatibility and atomic field/GIS tombstones added.
Build/lint passed (15s). Initial 103-test run exposed nine outdated schema-version
assertions. Exact fixture diff audit retained all 54 methods / 388 assertions in
the ten modified legacy classes; see SCHEMA_13_TEST_AUDIT.md. After fixture updates
and two Android import tests, 105 tests passed (76.158s). User-requested resume
rerun also passed: **105 tests, 90.226s**, `/sdcard/mastixa-resume-105-tests.txt`.
Bounded Android GeoJSON/KML/GML imports and manual geometry are implemented/tested;
native ParcelMapView compiles. Map/GPS/point UI/tracks remain incomplete; phases 4+
have not started.
Independently requested ArcGIS layer and its JSON/parent metadata
returned HTML HTTP 404; see GIS_PROVIDER_VERIFICATION.md. This is a dated environment
verification block, not a permanent service-unavailable conclusion.

Phase 3 stabilized on resume: Android map screen, foreground GPS, point CRUD,
durable segmented tracks, live OSM provider and connectivity handling added.
Desktop point CRUD and saved-track rendering added. Full Android **111 passed,
102.731s**; full Desktop **34 passed,174.833s**; build/lint passed, 0 errors /
8 existing warnings. Official OSM visible tiles verified on both clients.
See GIS_PHASE3_STATUS.md for exact commands and external/real-device limitations.
Current position: **Phase 4 coordinate exports in progress**. No additional
checkpoint created; existing `9cce2b6` and remote tag remain intact.

Phase 4 completed after resume verification. Desktop `tests.test_coordinate_exports`:
3 passed (0.668s), covering multi-field selection, source precision, negative
coordinates, holes/MultiPolygon, Unicode and output contents. Android export /
import / geometry / old reports: 14 passed (4.751s); finished export UI + core /
import / old reports: 11 passed (8.268s). Build/lint passed after replacing a
Java API 33-only stream helper with a compatible buffered copy. Actual Desktop
and Android PDFs rendered and inspected; pypdf extracted Greek names, EPSG and
all expected coordinates. Android XLSX independently opened with openpyxl:
numeric coordinate cells, text KAEK with leading zeros, no formula execution.
Current position: **Phase 5 reference CRS verification**. Phases 6–17 not started.

Phase 5 completed: Desktop 2 reference tests passed; Android 10 CRS/geometry/
import/export tests passed (4.393s) after fixing Proj4J acceptance of geocentric
CRS in the 2D workflow. Published numerical tolerances unchanged. Current position:
**Phase 6 offline sync contracts, local state and conflict-preserving integration**.
No configured Supabase account/dataset or credentials found/used; live end-to-end
verification requires external configuration. Implement/test the local contract
and transport abstraction using isolated fixtures first.

Phase 6 resume: Desktop and Android persistent sync journals, dataset-scoped
cursor/version state, incremental coordinator and explicit conflict resolution
implemented. Android schema 14 adds sync metadata; legacy fixtures retain all
57 tests / 403 assertions. Null deletion-date unboxing bug corrected. After a
usage-limit rejection, separate approved adb commands actually ran: Android
sync/GIS 8 passed (19.307s). Actual Python → Android → Python → Android file
exchange passed on Medium_Phone, including EPSG:2100 originals, derived WGS84,
GPS point/track, deletion/null handling, retries and identical final wire state.
See GIS_SYNC_VERIFICATION.md for exact evidence and the distinct live Supabase
configuration block. Current work: final divergent-polygon regression and full
Desktop/Android tests before Phase 7 checkpoint. Phases 7–17 remain not started.

Phase 6 completed under the specification's missing-Supabase fallback: full
Desktop **48 passed, 164.828s**; full Android **123 passed, 118.749s** including
divergent polygon edits, old migrations/backups and business/UI regressions.
Final Android build/lint succeeded (4s). Logs: `.tools/phase6-full-desktop-tests.txt`,
`.tools/phase6-full-android-tests.txt`, `.tools/phase6-final-build.txt`.
Phase 7 in progress: staged inspection and normal maps checkpoint/tag/push.
Current candidate scan: 264 files, 114 Android, no credential/forbidden-file findings;
Windows and Android source present. Original checkpoint remains intact.

Phase 7 COMPLETE: commit `404bd128d73becb10a64a9efc7c7a148b5eb6ccb`, annotated tag
`maps-before-full-qa`, both pushed normally to existing origin. Remote branch and
peeled tag match. Independent bare fetch tree `87de0358c4c10be53c4566bf42739d8af25a5b4a`
matches audited local tree exactly (264 files / 114 Android). Current position:
**Phase 8 full QA**; checklist in FULL_QA_CHECKLIST.md. Phases 9–17 not started.

Phase 8 update 2026-09-10: all pre-existing uncommitted changes preserved. Fixed
and retested live track drawing (7 tests) and Desktop tile retry/stale reply/
bounded decoding (3 tests). Real airplane-mode offline map/point/track/export
run passed 4/4 (6.734s); not repeated in the later cache-specific work.
The first cache run passed cache checks but host restore timed out; not treated
as a code failure. A coordinated real network cycle then exposed an Android
reconnect bug: uncached tiles never retried after the initial backoff redraw.
Small provider/callback fix passed the same live cycle 1/1 (9.328s), plus 5/5
affected map/lifecycle regressions (10.842s). Build/lint passed; debug build
passed. Emulator restored to Wi-Fi/data on, airplane off. See PHASE8_NETWORK_QA.md.
**Phase 8 remains incomplete** pending remaining audit/interruption cases and
final full suites after all fixes. User now explicitly requires no commit/tag/
push; propose the next safe checkpoint only after full Phase 8 completion.
