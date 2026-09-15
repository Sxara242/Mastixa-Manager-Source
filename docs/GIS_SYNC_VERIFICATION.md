# Phase 6 GIS sync contract and verification

The clients use profile-local SQLite records and explicit dataset UUIDs. The
version 1 wire contract carries stable UUIDs, created/updated/deleted timestamps,
parcel name/KAEK, original geometry and its actual EPSG CRS, GPS points and
segmented tracks. Each client derives WGS84 and measurements locally. Financial
records and the complete database are not uploaded by this GIS abstraction.

`SyncCoordinator` / `GisSyncContract.run` accept an injected transport. Pull uses
an incremental cursor; push uses a per-record remote version for compare-and-swap.
Content fingerprints detect field metadata edits as well as geometry changes.
Acknowledgements retain the sent fingerprint, so later edits remain pending.
Uncertain uploads are idempotent when retried. A transport must retain tombstones,
provide complete cursor batches, monotonically version records, scope all access
to the authenticated user's explicitly selected dataset, and atomically enforce
compare-and-swap. A future Supabase adapter must enforce RLS and use user sessions
and client-safe credentials. No service-role key belongs in either client.

Concurrent edits are conservatively journaled, including geometry and deletion
conflicts. No polygon merge or clock-based overwrite occurs. Both versions remain
in the profile database. Resolution explicitly selects `local` or `remote` and
rejects a stale local preview. Resolved journal entries remain for audit. Parent
deletion is blocked by unsynced child edits; accepted tombstones preserve payloads
and never physically delete the recipient's business field or finance data.

Desktop migration is additive (`gis_sync_v1`). Android schema 14 adds three sync
tables; schema 13 GIS data remains intact. Logical backups now include these
tables, while schema 2–13 snapshots follow their original table counts. Fixture
updates retain all **57 test methods and 403 assertions** in the twelve affected
existing files (including the helper with no tests). They only update current
schema expectations and remove new tables when constructing historical schemas.
The dedicated schema 13 migration/restore test exercises actual upgrade logic.

## Executed verification

- Desktop full suite: **48 passed, 164.828 seconds**, including contract, SQLite
  integration and divergent-polygon preservation/resolution.
- Android sync + GIS: **8 tests passed, 19.307 seconds**, after correcting an
  actual nullable `Long` unboxing bug in deletion-date serialization. The earlier
  four failures were production-code failures, not weakened test assertions.
- Updated Android build/lint succeeded. The initially rejected combined adb
  command did **not** execute and was never counted as successful. After resume,
  separate approved installation/instrumentation commands ran on Medium_Phone,
  exclusively against `gr.mastixa.manager.checks`.
- Final full Android suite: **123 passed, 118.749 seconds**, including all seven
  sync tests, GIS/export/CRS and existing business/UI/migration tests. Final
  assembleDebug/assembleChecks/assembleChecksAndroidTest/lintDebug succeeded (4s).
- Actual cross-runtime exchange completed: Python shared fixture → Android
  SQLite/point edit → Python SQLite/geometry, point tombstone and track edit →
  Android SQLite → independent Python final comparison. Three UUIDs, exact
  source EPSG:2100 coordinates and metadata, equivalent WGS84 geometry, correct
  null/tombstone state, and no duplicate upload/record after retries.
- Final exchange wire-state SHA256:
  `76b2daf11dcc6f6478241538aa4f6678badef54ebc75e9d400547945642d1a8e`.
  Maximum observed WGS84 coordinate difference: **2.1387336346379016e-12 degrees**,
  below the unchanged CRS reference tolerance of 2e-7 degrees.
- First actual exchange instrumentation: 1 passed (1.675s). Final real-file
  round-trip instrumentation: 1 passed (2.116s). The ordinary suite's final
  round-trip method uses a packaged fixture when no external argument is given;
  the above actual run explicitly supplied `sync_roundtrip` and read the real
  Python output, rather than counting the fixture fallback as the actual exchange.

Reproduction uses `GisSyncTest#desktopWireFixturePreservesSourceCoordinatesAndReturnsAndroidEdits`,
pulls its synthetic `gis-sync-android-return.json`, runs
`python -m tests.gis_exchange_check prepare ANDROID_RETURN WINDOWS_RETURN`, pushes
only that synthetic Windows return into checks external files, then runs
`GisSyncTest#desktopRoundTripConvergesAndRetriesDoNotDuplicate` with
`-e sync_roundtrip gis-sync-windows-return.json`. Pull the final Android JSON and
run `python -m tests.gis_exchange_check verify WINDOWS_RETURN ANDROID_FINAL`.
Every local database used by this procedure is synthetic and temporary.

## External limits

**BLOCKED EXTERNAL: live Supabase end-to-end verification.** No configured
Supabase project, authenticated user session, dataset association or RLS deployment
is available. The transport is a tested abstraction with isolated mock server;
the exchange above verifies the real client runtimes and SQLite implementations,
not a live cloud service. No live sync success or user-facing configured cloud
service is claimed. Backend adapter/configuration and its production UI must be
completed against the selected account before enabling live synchronization.
