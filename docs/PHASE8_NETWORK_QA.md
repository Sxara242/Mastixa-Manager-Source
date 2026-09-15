# Phase 8 — Android cache and network recovery

Updated 2026-09-10. No commit, tag or push was made during this QA work.
All earlier uncommitted Phase 8 changes were confirmed present before resuming.
The verified Phase 7 checkpoint remains `404bd12` / `maps-before-full-qa`.

**CURRENT STATUS: PHASE 8 COMPLETE for the configured local/emulator scope,
under the user's final verification instructions.** The final gate below
supersedes earlier chronological entries marked incomplete. Known external
limitations remain explicit; this is not completion of master phases 9–17.

## Final verification gate

- **Build PASS:** `assembleDebug assembleChecks assembleChecksAndroidTest`,
  together with `lintDebug`, completed successfully in **19s**.
  `.tools/phase8-final-android-build-lint.txt`.
- **Lint PASS: 0 errors, 12 warnings.** The current report is
  `android/app/build/reports/lint-results-debug.txt` (generated/ignored).
  Warnings concern available Gradle/test-runner updates, manifest backup/icon
  declarations and eight `SetTextI18n` findings in existing UI text. No lint
  suppression, baseline change or unrelated cleanup was used to pass the gate.
  The current count is 12; earlier historical warning counts are not substituted.
- **Focused runtime regressions PASS: 2/2, 5.446s.** Only these methods ran:
  `GisLifecycleUiTest.recreationPreservesViewportAndDurableTrackWhilePausingRecording`
  and `ParcelMapUiTest.deniedPermissionKeepsMapUsableAndViewportRestorable`.
  `.tools/phase8-final-focused-tests.txt`. They cover recreation, preserved
  viewport/durable track, pause/no stale restoration, permission denial and
  navigation after the last changes to GPS startup and callbacks.
- Existing successful real offline/cache/network/GPS, profile/export protection,
  rollback and cross-runtime round-trip evidence was retained. None of those
  cycles, the full Android suite or Windows/Python suites was rerun in this gate.
  The full 48 Windows / 123 Android baseline remains historical coverage for
  unchanged areas, supplemented by the subsequent focused Phase 8 checks.
- Reviewed the production diff and new instrumentation files. Host-controlled
  network/GPS/process tests are explicitly opt-in, live markers and failure
  injection remain in instrumentation, and no production test-only branch,
  debug override or disabled assertion was introduced. `git diff --check` passed.
  Generated APKs, logs, synthetic databases and build artifacts remain ignored.
- **No new bug; no application or test source changed in this final gate.**
  Only this report, `FULL_QA_CHECKLIST.md` and `MASTER_PROGRESS.md` were updated.

Previously completed later-change evidence, retained without rerunning:

| Check | Result / evidence |
|---|---|
| Windows export cancellation/failed write and SQLite sync rollback | 2/2; `.tools/phase8-storage-targeted.txt` |
| Android export ownership, queued save, finish/cancel, unavailable destination and SQLite rollback | 6/6; `.tools/phase8-failure-fixed-tests.txt` |
| Unavailable document picker and unmapped point deferred until parent can sync | 2/2; `.tools/phase8-followup-tests.txt` |
| Actual checks-process loss/reopen with durable geometry, pending sync and paused track | prepare 1/1, verify 1/1; `.tools/phase8-process-prepare.txt`, `.tools/phase8-process-verify.txt` |
| Packaged Windows startup/shutdown with isolated synthetic data | Build succeeded; executable smoke exit 0; `.tools/phase8-packaged-build.txt`, `.tools/phase8-packaged-data/data/logs/mastixa_manager.log` |
| Delayed network callbacks across profile contexts | 1/1; `.tools/phase8-context-tests.txt` |
| Actual disabled GPS → enabled service, stale/duplicate/profile callback protection | 1/1; `.tools/phase8-gps-fixed-tests.txt` |

**Checkpoint readiness: YES for the reviewed Phase 8 source/tests/docs**, with
the existing public-service/account/physical-device limits below retained.
No commit, tag, push or Phase 9 work has been performed. Future staging must
include only the reviewed source/tests/docs, not ignored local QA artifacts.

## Scope and evidence

The completed standalone offline run remains **4/4 passed, 6.734s**:
`.tools/phase8-actual-offline-tests.txt`. It asserted airplane mode and absence
of validated internet, with Wi-Fi disabled. It was not repeated during the
subsequent cache/recovery work.

The opt-in `AndroidNetworkRecoveryTest` exercises the real Android Activity,
network callbacks, `HttpURLConnection`, HTTP disk cache and OSM visible tiles:

1. Warm the visible tile cache online.
2. Host enables airplane mode and disables Wi-Fi after `READY_OFFLINE`.
3. A fresh provider instance loads the same tiles offline, with an actual
   increase in HTTP disk-cache hits (not retained in-memory bitmaps).
4. Pan once to a synthetic uncached area while still offline and wait for the
   failed requests to finish.
5. Host restores networking after `READY_RESTORE`.
6. Require tiles to load in the same Activity and map without a further pan,
   provider replacement or application restart. Compare full logical database
   snapshots before/after to prove no record changes.

The earlier manually coordinated run reached the cache success/restore stage
but timed out waiting for the host to restore internet. Its log is
`.tools/phase8-network-initial.txt` (111.025s). The emulator was subsequently
closed. That incomplete environment transition was not counted as a code bug
or a passed recovery test. A bounded host script now observes the test's explicit
stage messages and restores original networking in `finally`, including on failure.
Local helper: `.tools/run_network_qa.ps1` (ignored development artifact).

## Actual bug and fix

**Medium — Android uncached tiles did not recover after reconnect.** A completed
network cycle reproduced the failure in **60.741s**:
`.tools/phase8-network-code-failure.txt`. Internet returned, but the same map
did not load its uncached tiles within the unchanged 15-second recovery bound.

Root cause: failed tiles were suppressed for 30 seconds, yet no timer requested
a later redraw. The connectivity callback only invalidated the view; when that
redraw occurred during suppression, there was no subsequent attempt.

Small fix:

- `AndroidBasemap`: clear failure backoff on network return, schedule a bounded
  30-second retry for failures, ignore stale pre-reconnect failures for backoff,
  and retain failure entries only for visible tiles. Close still cancels timers,
  connections and workers.
- `ParcelMapView`: forward the network-return notification to its current provider.
- `ParcelMapActivity`: notify the provider on network availability/validation.
- `AndroidNetworkRecoveryTest`: preserve all recovery assertions; add a real
  disk-cache hit assertion. Choose a fresh synthetic uncached viewport each run
  so successful previous runs cannot mask the offline-miss/recovery scenario.

## Results after fix

- **FIXED AND RETESTED:** real online → offline/cache → online/recovery cycle,
  **1/1 passed, 9.328s**. All three stage markers reached, including `PASSED`.
  Log: `.tools/phase8-network-cycle.txt`.
- **TESTED AND PASSED:** affected provider/map/lifecycle regression selection,
  **5/5 passed, 10.842s** (`BasemapTest`, `ParcelMapUiTest`, `GisLifecycleUiTest`).
  Log: `.tools/phase8-network-related-tests.txt`. This rerun was justified by
  changes to provider callbacks and the map Activity; it did not rerun the
  standalone four-test offline suite.
- `assembleChecks assembleChecksAndroidTest lintDebug`: succeeded (48s).
  `assembleDebug`: succeeded (3s). Only checks APKs were installed.
- Final emulator settings verified: Wi-Fi **1**, mobile data **1**, airplane **0**.
- No production profile/database, credentials or Supabase data accessed/changed.

Reproduce the live test with the `live_network=true` instrumentation argument and
the two host-controlled stage transitions. Without that flag it explicitly uses
a JUnit assumption rather than silently claiming live network coverage. A final
full-suite run must account for this opt-in test separately or supply the flag
and coordinate the transitions.

## Remaining Phase 8 work

### Narrow resume: profile/context isolation (2026-09-10)

The working tree was inspected and all existing uncommitted changes retained.
`AndroidNetworkRecoveryTest.java` is still an untracked new file, so ordinary
`git diff -- <file>` is empty; its existing contents were read directly and
the successful live-cycle method was preserved.

- **PASS, retained evidence:** disk-cache reads and same-map network recovery,
  `cachedTilesOfflineAndUncachedTilesRecoverWithoutReopening`, 1/1 in 9.328s
  (`.tools/phase8-network-cycle.txt`). The production map/provider files have
  not changed since that successful run. No live network cycle was repeated.
- **PASS, retained evidence:**
  `ExportFailureUiTest.profileChangeCannotRestoreAnotherProfilesPreparedExport`
  in the prior 6/6 selection (`.tools/phase8-failure-fixed-tests.txt`, 14.719s).
  Prepared exports are bound to the saved profile ID; a different profile
  cannot restore the old staging file. This test was not repeated.
- **PASS, new targeted test only:**
  `AndroidNetworkRecoveryTest.lateRecoveryCallbacksCannotRestorePreviousProfileContext`,
  **1/1 in 4.612s** (`.tools/phase8-context-tests.txt`). Two synthetic profiles
  deliberately share a field UUID but contain different polygons and points.
  Late callbacks from the closed old context and a network-return callback to
  the new context leave the new profile's rendered polygon/point intact, with
  no old GPS fix/track, no stale provider redraw and byte-identical logical
  database snapshots for both profiles. Callback delivery is injected; actual
  offline/online delivery remains covered by the prior successful live test.
- The shared HTTP cache contains public basemap tiles by URL, not profile
  geometry, GPS records or prepared exports. This matches the current design.
- Instrumentation APK build succeeded (4s). No production code changed in this
  narrow resume. A test-only compilation error from a non-public SDK method
  was corrected before execution; it was not an application failure.
- No Windows/Python suite, full Android suite, standalone offline test,
  sync rollback, round-trip, emulator restart, network toggle, commit or push
  was performed in this resume.

**The requested cache/network/profile-context check is complete; stop here.**
Phase 8 as a whole is still incomplete and is **not ready for its final
checkpoint**. The previously queued GPS service-recovery check has not run,
and final affected-area verification/build/lint after the later export/sync
changes remains pending. Those tasks are outside this narrow request. The
earlier permission-grant attempt was rejected by automatic review due to a
usage limit before permissions or the location setting were changed; that
does not constitute a GPS test result. No GPS fix is attempted in this resume.

**Phase 8 is not yet complete.** The cache/network recovery subtask is complete.
The existing checklist still requires remaining error/interruption/database and
old-feature audit coverage, including any new findings, followed by the final
complete Windows/Android suites and build/lint after all Phase 8 fixes.
The previous full baseline (48 Windows / 123 Android) remains valid historical
evidence, not a claim that the complete suite was rerun on these latest changes.
Real GNSS field accuracy/power needs a physical device; live Supabase remains
unverified without an account/dataset and does not block local QA.

Per the user's latest instruction: keep changes uncommitted, do not push, and
propose a safe checkpoint only after Phase 8 and its final tests are complete.

## GPS service-only resume — completed

This entry supersedes the pending GPS-service status above. Existing Phase 8
changes were inspected and preserved. No previously passed tests were rerun.

**FIXED AND RETESTED — GPS disabled-service recovery.** The existing focused
`GpsServiceRecoveryTest.disabledGpsKeepsStatusAndRecoversWithoutReopening`
failed against the previous application code in 1.951s:
`.tools/phase8-gps-before-tests.txt`. The freshness refresh replaced the actionable
disabled-service message with a generic waiting-for-fix message. Inspection
also confirmed that `startGps()` returned before registering a listener when
the GPS provider existed but was disabled, so the screen could not receive
`onProviderEnabled` and recover by itself.

Minimal related changes in `ParcelMapActivity.java`:

- Register for provider callbacks even while the existing GPS provider is disabled.
- Keep the disabled-service message during periodic freshness refreshes.
- Clear the displayed fix when starting a GPS session and reject samples whose
  monotonic timestamp precedes that session; invalidate the old session when
  the provider is disabled.

The same focused test was extended without removing its original assertions.
With actual emulator location **disabled**, it requests GPS, verifies the
disabled message and listener, then emits `GPS_QA_READY_ENABLE`. The host enables
location and the unchanged Activity receives recovery callbacks without restart.
After that real service transition, controlled Location samples verify that a
still-fresh sample from before activation cannot return, repeated delivery of
one fresh sample produces exactly one track position, no point records are
created implicitly, and a queued callback after a session/profile switch cannot
write another track position. Recovery alone leaves the logical DB snapshot
unchanged. Live location updates are stopped before deterministic sample injection
to avoid mixing emulator-generated fixes into those record-count assertions.

**PASS: 1/1, 24.610s**, `.tools/phase8-gps-fixed-tests.txt`.
Only this GPS test method ran: once before the fix (FAIL), once after (PASS).
Checks application/instrumentation builds succeeded (6s, then test-only 2s).
No full suite, Windows/Python tests, final lint/regression, network/offline test,
emulator restart/reset, commit or push was performed. Location was restored to
**enabled**, and both checks-app location permissions to their original **denied**
states. The main application and real profiles were not modified.

Files changed in this resume: `ParcelMapActivity.java`,
`GpsServiceRecoveryTest.java`, and this report. Physical GNSS accuracy/power and
live Supabase remain the previously documented external verification limits.

**GPS service check COMPLETE. Stop here.** The outstanding local Phase 8 gate is
final verification of the later export/sync/GPS changes and required build/lint,
including reconciliation of the QA checklist with retained successful evidence.
Phase 8 itself is not yet COMPLETE and no final checkpoint has been created.
