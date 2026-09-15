# Phase 2 checkpoint evidence — 2026-09-09

Desktop source remains in its original layout. Android source was copied from
the sibling project and verified byte-for-byte before portability/lint changes.
The sibling remains intact; further development uses this repository's `android/`.

## Actual checks

- Windows: `.venv/Scripts/python.exe -X utf8 -m unittest discover -s tests -v`:
  **25 passed, 228.255 seconds** (includes all existing pages, profile switching,
  language, reporting, finance/stock relationships and Android exporter).
- Android: `gradlew.bat testDebugUnitTest lintDebug assembleDebug assembleChecks
  assembleChecksAndroidTest --console=plain`: **BUILD SUCCESSFUL, 29 seconds**.
  JVM unit test task explicitly reports **NO-SOURCE**, not tests passed.
- Lint: initially 59 errors (57 newer Java API calls and two navigation reports).
  Core library desugaring 2.1.5 supplies Stream.toList / Collection.toArray on
  supported older Android versions. Welcome now registers the API 33+ platform
  back callback; legacy fallback is retained. Main already registered that callback.
  Narrow lint annotations explain the legacy overrides, with no global baseline.
- Final lint: **0 errors, 8 warnings**: newer AGP/dependency available, missing
  application icon, data extraction rules, four text composition warnings.
  These remain for the ordered QA phases; dependency updates are not applied blindly.
- Full original Android instrumentation suite: **96 passed** in Phase 0.
  Post-integration full regression (including system Back during profile creation):
  **96 passed, 93.385 seconds**, `/sdcard/mastixa-checkpoint-tests.txt`.
  Integrated main APK installed with `install -r`: Success; Welcome Status: ok.
- Pre-stage pattern scan: **211 candidate files, 10 ZIP fixtures, 212 reachable
  historical blobs**, zero credential/forbidden-file findings. Password-like
  application identifiers are runtime inputs; tests use explicit synthetic values.
  This is a bounded source/history review, not a guarantee that no secret exists.
- Existing remote branch `refactor/pages` was `efb88d7`; local HEAD `9db4e41`
  descends from it. No checkpoint tag collision observed in remote tag listing.

## Intended checkpoint contents / exclusions

Include preserved desktop fixes/exporter/tests/version metadata, Android source,
wrapper/configuration, synthetic ZIP fixtures, licensed OCR models/notices,
README/master ledger/specification and minimal dual-client CI.
Exclude user databases/profiles/backups, SDK/JDK/tool scripts/caches, local SDK
configuration, emulator files, generated APK/builds and signing credentials.
No release APK is published by CI. Normal pushes succeeded to configured origin
`https://github.com/Sxara242/Mastixa-Manager.git`: branch `refactor/pages` and tag
`android-before-maps-qa` resolve to `9cce2b61889bee39f14138482aac5ed0dc152aa0`.
Independent remote bare clone has the same audited tree hash
`b8b39ac7d33d4b4a667e482ec5f8acb940b390e8` (212 files, 90 Android files).
Rechecked committed tree and ZIP fixtures: zero credential-pattern or forbidden
path findings. Windows and Android source/configuration are present remotely.
Anonymous GitHub API returned 404; hosted CI run status remains unverified.

## Primary references consulted for fixes

- [Google desugar_jdk_libs changelog](https://github.com/google/desugar_jdk_libs/blob/master/CHANGELOG.md)
- [Android platform predictive-back migration](https://developer.android.com/guide/navigation/custom-back/predictive-back-gesture)
- [Gradle Actions wrapper validation](https://github.com/gradle/actions/blob/main/README.md)

Real-device/minimum-API runtime testing remains for the full QA phase.
