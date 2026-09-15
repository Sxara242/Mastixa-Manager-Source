# Pre-release bug audit — 2026-09-12

Baseline: `8ae808d9cfa756cb4e1a41b5f7ee98bea04007c5`, branch `refactor/pages`.
Scope: repository inspection and targeted reproductions before Phase 16I.
This is not a claim that all possible runtime scenarios or all repository lines
have been tested. During targeted investigation no full suites or completed CSV/offline/update/
release gates were rerun. The final resume explicitly requires fresh normal
Desktop + Android CI after pushing the audit checkpoint. Phase 16I has NOT started.

## Retired guide

`1a5e514`: removed `MASTER_EXECUTION_PLAN.txt` after checking repository references.
Its only consumer was the link in `MASTER_PROGRESS.md`; no application/test/CI/
packaging dependency was found. Retained operational constraints and links to
GIS/CRS/sync/QA evidence are in that ledger. Its old numbering is explicitly
historical, not another current roadmap.

## Proven findings and fixes

| Finding | Severity / root cause and reproduction | Fix / regression / commit |
|---|---|---|
| Backup collision | High: manual/safety paths had second-only timestamps; two snapshots at a fixed clock overwrote the first. | Exclusively reserve a unique filename; both snapshots retain their contents. `test_same_second_backups_preserve_both_snapshots`, `97d0073`. |
| Restore retention deletes active inputs | High: pruning ran before restore, able to remove selected pre-restore input and recovery snapshot (zero retention reproduced). | Prune only after success, protect input/current safety; failure retains rollback files. Injected partial-write rollback and successful zero-retention regressions. `97d0073`. |
| Malformed profile manifest escapes error handler | Medium: JSON null/list/string and null integer fields raised AttributeError/TypeError instead of ProfileError handled by settings UI. | Validate object and numeric conversions before writing; five malformed fixture subcases verify unchanged registry and no profile directories. `test_malformed_manifest_returns_profile_error_without_creating_data`, `2b585ee`. |
| Literal paths interpreted as SQLite URI syntax | High: unescaped `#`/`%` in directory names truncated/decoded URI paths; `#` also hid `mode=ro`, allowing creation of an unintended empty file. Reproduced failed backup/import under `Κτήμα #1 %25`. | Resolve and percent-encode all four read-only backup/profile URI paths with `Path.as_uri()`. Two round-trip regressions, including no truncated-path artifact. `20c1388`. |
| Interrupted profile export destroys previous destination | High: ZIP opened final destination with `w` before archive completion. Injected OSError on member write replaced prior complete export with partial ZIP. | Same-directory private temporary archive, atomic replace only after ZIP close, cleanup on failure. `test_interrupted_profile_export_preserves_previous_destination`, `b102d93`. |
| Mixed Android export snapshot | Medium: field name/KAEK read before geometry transaction. WAL writer changing metadata+geometry atomically reproduced old name with new geometry. | Move field read inside existing transaction; no new transaction framework. `snapshotKeepsFieldMetadataAndGeometryInOneTransaction`, `2dd6361`. |

All six were reproduced before fixing. No assertions/tolerances were weakened.
No schema/version change. No real profile/database contents were modified.

## Actual targeted execution

Windows prefix: `.venv/Scripts/python.exe -X utf8 -m unittest`.

- Initial two backup regressions: FAIL 2/2, as expected before the fix.
- `tests.test_phase16d_backup_restore`: PASS 5/5 after first fix;
  extra successful-retention method PASS 1/1.
- Malformed manifest method: FAIL 1 method / 5 error subcases before fix;
  `tests.test_profiles`: PASS 3/3 afterwards.
- Two URI-path methods: FAIL 2/2 before fix.
- `tests.test_phase16d_backup_restore tests.test_profiles`: PASS 11/11,
  2.636s after URI fix (7 backup + then 4 profile tests).
- Interrupted profile-export method: FAIL 1/1 before fix;
  final `tests.test_profiles`: PASS 5/5, 1.368s afterwards.
- Direct backup consumers, one selected method each: PASS 3/3, 3.241s:
  - `tests.test_crop_program_backup.CropProgramBackupTest.test_sqlite_backup_round_trip_preserves_phase12_state`
  - `tests.test_plant_tracking_store.PlantTrackingStoreTest.test_windows_sqlite_backup_restore_includes_plant_registry_and_events`
  - `tests.test_inventory_quality_gate.InventoryQualityGateTests.test_backup_restore_preserves_inventory_provenance_expense_and_triggers`

Final valid Windows evidence covers **15 distinct tests: 15 PASS** (7+5+3).
This is a union of targeted runs, not a new 15-test or full-suite command.
Expected injected-error log messages are not test failures.

Android command, using JDK21 and local SDK:

```
./gradlew.bat connectedChecksAndroidTest '-Pandroid.testInstrumentationRunnerArguments.class=gr.mastixa.manager.CoordinateExportTest#snapshotKeepsFieldMetadataAndGeometryInOneTransaction' --console=plain
```

Before fix: FAIL 1/1 (`New field` expected, `Old field` returned).
After fix: **PASS 1/1**, 0 errors/failures/skips, XML time 9.961s;
Gradle BUILD SUCCESSFUL 35s, includes required checks/test compilation.
Only an isolated `.checks` synthetic UUID-named database was created/deleted.
Emulator started without wipe/reset; no main-app reinstall, pm clear, permission
loosening, AV changes or network/GPS test repetitions.
No new lint/full Android/Windows gate is claimed.

## Inspection coverage and evidence boundaries

Everything marked inspection below is **UNVERIFIED as new runtime QA**. Retained
prior evidence remains valid for unchanged paths but is not a new PASS.

| Area | Inspected files / result / limits |
|---|---|
| DB/migrations/transactions | `database.py`, `gis/store.py`, `gis/sync_repository.py`, crop/plant/sensor stores; Android `FarmStore`, `LocalBackup`, `GisSyncRepository`. Reviewed additive schemas, version dispatch, foreign keys, tombstones, explicit transactions and restore staging. Sensor executescript is used on fresh store/ingestion connections before business writes; no caller-owned transaction bug demonstrated there. Interrupted migration across every old schema NOT newly injected. |
| Production/money/year locks | `production.py`, `sales.py`, inventory lock call sites, `year_lock.py`; Android `YearLocks`/import integration. Windows checks original and target year, Android triggers check OLD/NEW and linked writes. Enforcement is not architecturally identical: Windows UI guards vs Android SQL guards; concurrent/direct SQL bypass on Windows UNVERIFIED. Reviewed existing cross-module validation tests; no rerun. |
| CSV | `data_export.py`, Android `WindowsImport`, `CatalogImport`, `ProductionImport`, Phase16CsvImport tests/docs: bounded ZIP/UTF-8, required/duplicate columns, finite values/date/identity rules, transactional apply. Retain 16A Windows 4/4, Android 9/9 supplied evidence; no related code changed. No claim of generic symmetric CSV round-trip (feature sets differ). |
| Geometry/CRS/parcels | `gis/geometry.py`, `importers.py`, `exports.py`, `store.py`; Android `GeoStore`, `CoordinateExport`; CRS/GIS docs/tests. Ordered rings, original vs normalized coordinates, known EPSG/axis contract, bounded archives, XML protection, revision checks and soft deletion reviewed. Android Shapefile/DXF still needs Desktop conversion. No fresh CRS/GIS round-trip run. |
| GPS/offline/network | `gis/tracks.py`, `map_view.py`; Android `GpsTrack`, `ParcelMapActivity`, `AndroidBasemap`, `MapProviders`. Reviewed durable fixes/segments, paused recovery, stale-fix guard call sites, visible-tile limits, cache, request generation, callback close/retry handling. Retain prior real offline/cache/GPS PASS; no new service transitions. |
| Sync | GIS contracts/repositories on both clients, identity/sync docs: dataset+UUID, canonical payload/hash, revisions, expected hash, conflict preservation, transactional apply/ack and pending parent handling. Existing integer-vs-UUID mapping is deliberate. No new live transport verification. |
| Profile isolation/lifecycle | `profile_manager.py`, settings import handler, Android `CoordinateExportActivity`, `SensorDataActivity`, `PlantTrackingActivity`, `ParcelMapActivity`, corresponding tests. Session/profile checks and export ownership examined; malformed packages and atomic export fixed. Full process-death/dialog/provider matrix UNVERIFIED in this audit. |
| Import/export/cancellation | Desktop GIS staging uses same-directory replace; profile ZIP lacked this and is now fixed. Android SAF fallback/temp cleanup reviewed; actual snapshot concurrency fixed/tested. Arbitrary third-party SAF providers can leave partial destination on failed writes, already disclosed; no broad provider guarantee. |
| Backup/restore | Real focused tests above, plus Android staged validation/AtomicFile recovery/transactional replacement and schema counts inspected. Full Android restore/update already green and unchanged. Storage failure during rollback itself cannot be guaranteed recoverable. |
| Windows startup/packaging | `runtime_paths.py`, `installer/MastixaManager.iss`, packaging scripts/spec and gate privacy filters: per-user data path separate from install path, stable AppId, lowest privileges, only pyproj database exception. Packaging files unchanged; no release-gate rerun. |
| Security/privacy | Manifest exported components/permissions, session checks, profile archive named-member extraction, geometry ZIP/XML bounds, app logging redaction and .gitignore inspected. No arbitrary archive path extraction found in inspected importers. Pattern scan of 435 tracked paths: no live DB/APK/AAB/local.properties/signing artifacts; no private-key/GitHub-token/AWS-key/JWT pattern matches in scanned text types. This is not proof of absence of all secrets or a historical secret audit. |

## Baseline CI and remaining risks

`gh run view 34714178335` independently confirmed CI #142 SUCCESS on baseline:
Desktop SUCCESS + Android SUCCESS. User-supplied Android update gate #4 and
Windows release gate #13 attempt 2 remain retained PASS; not rerun.
At the interrupted investigation boundary the six local audit commits had not
been pushed. The final resume preserves those commits and adds this report, then
pushes `refactor/pages` normally. Fresh verification is the `verify.yml` run
whose headSha matches that final checkpoint; its outcome must be read from
GitHub Actions and reported separately, never inferred from baseline #142.
That workflow runs the full Desktop unittest discovery and Android unit-test
task, lint, debug build and instrumentation compilation; it does not execute
the full Android instrumentation suite. Release/update gates are excluded.

Explicit remaining review/manual items:

- Physical GNSS accuracy/power and real field reception: UNVERIFIED.
- Live Supabase account/dataset/RLS, official Cadastre schema/query, configured
  licensed imagery/offline packs: external verification still unavailable.
- Profile ZIP import streams profile.db/avatar without an explicit decompressed
  size ceiling (manifest is bounded). Resource-exhaustion behavior is UNVERIFIED;
  assess an appropriate supported size policy in security review, not by deleting
  user data or creating a huge archive during this audit.
- Generic exception logging redacts local paths, not every possible business
  value in arbitrary exception messages: privacy review remains necessary.
- Simultaneous app processes/restore/retention operations and power loss during
  filesystem replacement are not newly stress-tested. Do not infer that the
  single-operation rollback tests cover every storage failure.
- Sensor ingestion docs describe rejecting new observations while disabled;
  implementation conservatively rejects observation-bearing replay batches too.
  No data corruption demonstrated; reconcile intended replay policy separately.

No unresolved reproduced failure remains after the targeted fixes. This audit
checkpoint is suitable for review and proceeding to the **separate Phase16I
security/privacy audit**, not a final public-release approval. Hosted CI for the
new commits and the explicit external/manual limits remain release verification
items. Phase16I was not started. No full-suite result is fabricated.
