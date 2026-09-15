# Schema 13 fixture audit after resume

Compared all modified existing Android test files against checkpoint `9cce2b6`.
An exact transformation comparison confirmed that their entire diffs consist only
of the following schema-related updates; no other test logic changed.

1. A current database now legitimately reports schema 13 because
   `FarmStore.onUpgrade` adds `gis_records` for versions below 13. Nine existing
   migration tests still asserted 12; their assertions now require 13. They still
   create the same older database versions and reopen them through FarmStore.
2. Synthetic legacy backup builders remove `gis_records` along with the other
   tables absent from their historical version. Without this removal a backup
   labeled schema 2–11 would incorrectly contain a schema-13 table.
3. `LegacySchema.dropStage12` also drops the newly added GIS table when deliberately
   constructing an older test database. No production migration is bypassed.
4. Corrupt-*current*-backup fixtures using `envelope(e,p,12)` now label the current
   payload as 13. Their malformed values/relationships and expected rejection are
   unchanged. This ensures rejection tests reach domain validation rather than
   succeeding prematurely because of a mislabeled table count.

The ten modified test classes retain **54 test methods and 388 assertions**,
identical to the checkpoint. The helper retains no assertions. No tests disabled,
no assertions removed, no expected failure converted to success, no production
validation relaxed. Backup validation adds GIS checks and preserves existing ones.

Additional coverage: 4 geometry tests, 3 GeoStore tests (12→13 migration, legacy
restore, conflicts/rollback, field tombstones), and 2 import tests. Full suite is
therefore 96 + 9 = **105 tests**.

Before resume, the first 103-test run failed in the nine stale version assertions.
After fixture updates and the two import tests, `/sdcard/mastixa-gis-storage-final-tests.txt`
reported **105 passed, 76.158 seconds**. The user explicitly requested another full
run; `/sdcard/mastixa-resume-105-tests.txt` is the new run and must be checked before
continuing implementation. Do not infer its result from the earlier run.

Requested resume rerun completed on 2026-09-09: **OK (105 tests), 90.226 seconds**.
Fresh `assembleChecks assembleChecksAndroidTest` succeeded before installation;
both isolated checks APK installs succeeded on Medium_Phone / emulator-5554.
Command: `adb shell am instrument -w gr.mastixa.manager.checks.test/androidx.test.runner.AndroidJUnitRunner`
(output redirected to `/sdcard/mastixa-resume-105-tests.txt`). The actual terminal
summary was read before any further implementation.
