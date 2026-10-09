# Development, CI and packaging

Windows source development uses Python 3.14/PySide6. Android uses JDK 21,
Gradle 8.13, AGP 8.13.2 and SDK 36. Windows is the current release target;
Android debug builds do not qualify a public Android release.

Run Windows tests from the root with `QT_QPA_PLATFORM=offscreen`, `PYTHONUTF8=1`
and `MASTIXA_DATA_HOME` pointing to a new disposable directory:

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements-dev.txt -c requirements-windows-rc.txt
.\.venv\Scripts\python.exe tools/run_windows_tests.py --jobs 2 --timeout 120 --module-timeout tests.test_stabilization=360
.\.venv\Scripts\python.exe tools/audit_public_source.py
.\.venv\Scripts\python.exe packaging/validate_windows_release.py
```

`requirements-dev.txt` includes Pillow for the optional image-fixture tools.
It is a development dependency, not a new Windows shipping input. Its original
MIT-CMU terms remain applicable; see [Pillow](https://pypi.org/project/pillow/).

Use synthetic fixtures and temporary profiles. Shared changes require
Windows/Android parity consideration. Android commands are in
[INSTALLATION.md](INSTALLATION.md). Instrumentation uses the `.checks` app.
The runner executes every `test_*.py` module in a fresh process and bounds each
module to 120 seconds, with an explicit 360-second stabilization override. That
legacy module constructs the complete window for 23 tests; measured assertions
completed in 284 seconds before fixture-controller cleanup. The override preserves
every assertion and still fails on timeout, failure or unsuccessful process exit.
Timeout diagnostics capture a Python stack before process-tree cleanup. This avoids
carrying Qt objects/timers from deleted
fixtures across modules. A failed module or timeout fails the run; no tests are
silently skipped. Both unittest classes and the existing plain test functions
are executed. Direct unittest discovery remains available for diagnosis but does
not discover those plain functions.

The hosted command also names three measured slow-module bounds: activity-expense
sync 240 seconds, composed UI localization 180 seconds, sale sources 360 seconds.
Each made assertion progress up to the original hosted bound and passes locally.
These explicit limits preserve all cases and fail on unsuccessful process exit;
they are not skip/xfail policies. Hosted CI must pass the complete corpus.

## Hosted CI

`verify.yml` runs Windows tests/packaging contracts on `windows-latest` and source
audit/Android build/lint/test-APK compilation on `ubuntu-latest`.
`windows-release-gate.yml` is a manual packaging check, without installers.
`android-runtime.yml` manually runs Linux emulator instrumentation.
`android-update-gate.yml` manually builds QA APKs with optional upload.
All workflows have read-only repository permissions, bounded runtimes and
nonpersistent checkout credentials. They require no production secrets.
Regular CI uploads no artifacts; optional manual artifacts expire after one day.
No dependency caches are created. Temporary artifacts cannot be the only
corresponding-source delivery mechanism for distributed binaries.

## Qualified Windows packaging

The actual recipe is `packaging/build_release.ps1` / `MastixaManager.spec` with
TLS/CRT/EPSG/Mesa guards. It uses locked PSF CPython 3.14.8 and FireDaemon
OpenSSL 3.5.9, wheel hashes in `requirements-windows-rc-hashed.txt` and supplier
identities in `packaging/windows-tls-inputs.json`. Preserve all locks.
Stock setup-python is for source tests, not qualified binary packaging.

Supplier roots/build venv must be independently provisioned at the relative
locations in the TLS lock. Supplier binaries and matching dependency-source
archives are not bundled in this snapshot. Public automated supplier bootstrap
and hosted frozen/installer qualification are still pending. Do not relax hashes,
copy ambient PATH DLLs or use an unqualified runtime to get a green result.

After prerequisites and owner authorization, invoke the existing build script
with distinct work/dist/installer paths. Before any binary upload, verify the
actual bundle, CRT/TLS/Mesa, real EXE smoke (`smoke_test_packaged.ps1`), installation,
upgrade/repair/uninstall/data preservation, EPSG/PDF/GIS/native routes and owner
acceptance. Bind source/SBOM/checksums to that exact artifact. Deliver required
covered source, patches, controlling build scripts and replacement instructions
with durable equivalent access. Source tests alone cannot approve publication.

Retained details: [distribution source](DISTRIBUTION_SOURCE.md),
[source delivery](SOURCE_DELIVERY_PLAN.md), [replacement](WINDOWS_LIBRARY_REPLACEMENT.md),
[CRT](WINDOWS_CRT_NORMALIZATION.md), [EPSG remedy](WINDOWS_EPSG_REMEDIATION.md).
Historical local archive paths are evidence references, not public downloads.
Use [RELEASE_STATUS.md](RELEASE_STATUS.md) for the current decision.
