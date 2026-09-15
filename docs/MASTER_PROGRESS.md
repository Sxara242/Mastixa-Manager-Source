# Master execution ledger

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
