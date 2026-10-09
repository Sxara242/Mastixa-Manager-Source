> Retained historical engineering record, sanitized for public review.
> Current status: [RELEASE_STATUS.md](RELEASE_STATUS.md). This record does not
> establish approval of the current source or a new binary release. Local-only
> receipt paths refer to privately retained evidence, absent from this snapshot.

# B2 canonical CRT deployment — 2026-10-08

**B2 PASS.** RELEASE-INFRA / DESKTOP, Windows x64 only. B1/B3/B4 remain
BLOCKED; B5 PASS is retained unchanged. **BLOCKED BEFORE RC BUILD.** No final
RC, commit, push, tag, publication, global installation or antivirus change.

The chosen deployment ships **zero Microsoft CRT DLLs and zero VC Redist
installers**. Recipients independently install Microsoft's official x64 Visual
C++ v14 Redistributable, **14.51.36247.0 or newer**, before Mastixa Setup.
`installer/vc_redist_prerequisite.iss` checks Installed/version in both registry
views and all five canonical System32 files before installation. Missing/older
prerequisites stop Setup with the official download-page address. There is no
automatic download, installer execution, elevation, reboot or global change.
The minimum is the exact qualified runtime; this batch does not establish the
oldest theoretically compatible runtime. Portable executable use has the same
documented prerequisite and cannot rely on Python starting without it.

## Exact old cases and causes

All original suppliers and 23 locked wheels remain byte-unchanged. Old shipping
paths in this table are removed by the build policy, not deleted from suppliers.
The full name-level PE normal/delay importer graph, symbol list, source hashes
and actual loaded-path attribution are in sibling
`WindowsB2NormalizationEvidence/pe-graph.json`, `crt-cases.json`, and
`baseline-final.json`. `windows-crt-normalization.json` is the checked-in mapping.
Duplicate canonical names cannot be assigned to a particular directory by the
PE table alone: Windows may reuse a previously loaded module with that name.

The retained PySide supplier packaging recipe explicitly calls
`download_qt_dependency_dlls(..., msvc_redist)` for both shiboken and PySide;
its Windows wheel file list includes those CRT names. The recipe's Qt CI
dependency archive is `pyside_qt_deps_684_64_2022.7z`. The source intent,
exact wheel membership and direct PE imports jointly establish intentional
vendoring. This is not a claim that a new executed producer receipt or older
Microsoft-original correspondence was obtained. The scoped recipe/hash receipt
is `WindowsB2NormalizationEvidence/pyside-crt-packaging-recipe.json`.

| Former path under `_internal/` | Cause and actual encoded dependency | Chosen result |
| --- | --- | --- |
| `PySide6/MSVCP140.dll` | Essentials6.11.2 wheel intentionally includes the Qt-signed14.44.35211.0 file.20 shipping PEs import canonical `MSVCP140.dll`, including QtCore/Gui/Widgets/PDF and bindings. Baseline selected the shiboken copy. | NOT SHIPPED; official canonical system runtime |
| `PySide6/MSVCP140_1.dll` | Same wheel/version;4 PEs import canonical `MSVCP140_1.dll`; baseline loaded this Qt-local copy. | NOT SHIPPED |
| `PySide6/MSVCP140_2.dll` | Same wheel/version;Qt6Gui imports canonical `MSVCP140_2.dll`; baseline loaded this Qt-local copy. | NOT SHIPPED |
| `PySide6/VCRUNTIME140.dll` | Same wheel/version;104 PEs import canonical `VCRUNTIME140.dll`; baseline reused the root CPython copy. | NOT SHIPPED |
| `PySide6/VCRUNTIME140_1.dll` | Same wheel/version;25 PEs import canonical `VCRUNTIME140_1.dll`; baseline reused the shiboken copy. | NOT SHIPPED |
| `shiboken6/MSVCP140.dll` | shiboken6.11.2 wheel intentionally includes Qt-signed14.44.35211.0 canonical CRT; same20 name-level edges; baseline loaded this copy. | NOT SHIPPED |
| `shiboken6/VCRUNTIME140.dll` | Same wheel/version;same104 canonical-name edges; baseline used root copy. | NOT SHIPPED |
| `shiboken6/VCRUNTIME140_1.dll` | Same wheel/version;same25 canonical-name edges; baseline loaded this copy. | NOT SHIPPED |
| root `VCRUNTIME140.dll` | Official PSF Python3.14.8 runtime14.51.36247.0;exact installed Microsoft Redist bytes;baseline loaded it. | NOT SHIPPED |
| root `VCRUNTIME140_1.dll` | Same official PSF runtime/version/correspondence;baseline reused shiboken-local copy. | NOT SHIPPED |
| `Shapely.libs/msvcp140-90bc62d4947a5878f1dc1057312f3be2.dll` | Shapely2.1.2 wheel's DELVEWHEEL receipt:1.11.1 repair, GEOS3.13.1 bin add-path. GEOS and GEOS_C actually import that exact14.44.35215.0 hashed name;baseline loaded it. | NOT SHIPPED;2 third-party DLL imports normalized |
| `numpy.libs/msvcp140-a4c2229bdc2a2a630acdc095b4d86008.dll` | NumPy2.5.3 wheel's DELVEWHEEL receipt:1.11.2 repair, producer OpenBLAS add-path. `_multiarray_umath` and `_pocketfft_umath` actually import that exact14.40.33810.0 hashed name;baseline loaded it. | NOT SHIPPED;2 NumPy extension imports normalized |
| `pyproj.libs/msvcp140-7c26614e1d733892c2deac7e245ce115.dll` | pyproj3.8.0 wheel's DELVEWHEEL receipt:1.13.0 repair, `C:/Windows/System32` and vcpkg bin add-path. `proj_9` actually imports that exact hashed name;bytes match official14.51.36247.0;baseline loaded it. | NOT SHIPPED;1 third-party PROJ DLL import normalized |

The three names come from delvewheel's vendoring/name-mangling process, which
isolates dependency versions and avoids DLL-name collisions. They are not mere
unused files in wheel layouts. A canonical Redist installation cannot satisfy
the unchanged hashed names. The originals are no longer shipping, so no
Microsoft filename-rename permission or older-file grant is relied upon.
The 44 existing OS-provided UCRT/API-set exclusion records remain unchanged.

## Deterministic third-party transformation

`packaging/crt_policy.py` and `windows-crt-policy.json` reject a changed/missing
old CRT input, changed importer, unknown CRT collection, duplicate destination,
unsupported architecture, Authenticode-signed importer or bound import table.
Only five unsigned third-party files are transformed: the2 NumPy extensions,
GEOS/GEOS_C, and PROJ. The exact PE import-string slots become
`msvcp140.dll`, padded with zeros; the PE checksum is recalculated. Length,
sections, code, other imports and all Microsoft bytes are preserved. Exact
upstream/output SHA256 locks make this fail closed and reproducible. This is a
third-party binary transformation, not a claimed upstream rebuild. The build
creates derived outputs in its work directory and excludes all13 original CRTs.
Post-COLLECT validation requires the5 exact transformed hashes and no CRT DLLs.

The original wheel provenance remains valid for inputs; the5 derived output
files are explicitly no longer represented as pristine wheel RECORD matches.
Modified source/build materials include the checked-in transformer/hash lock
and retained original GEOS/PROJ/NumPy sources and wheel receipts. Existing B4
source/replacement gaps remain unchanged; this B2 result does not close them.
Separately generated diagnostic local-version wheels have regenerated RECORDs,
fixed ZIP timestamps and identical hashes across two independent serializations.
They are marked `+mastixa.b2diag1`, not installed or promoted to the wheel lock.

Fresh upstream builds with `delvewheel repair --exclude msvcp140.dll` are the
preferred future supplier route. `--no-mangle msvcp140.dll` is an app-local
alternative only with licensed canonical files. Those repair options do not
undo an already repaired wheel. Current supported PySide/shiboken6.11.2,
NumPy2.5.3 and pyproj3.8.0 have no newer compatible release. The compatible new
Shapely2.2.0 wheel (GEOS3.14.1, delvewheel1.13.1) still vendors/imports hashed
MSVCP; it is neither a B2 fix nor adopted. No package was broadly upgraded.

## Runtime and redistribution classification

| Resulting dependency | Classification |
| --- | --- |
| All13 former Microsoft file cases | NOT SHIPPED |
| `msvcp140.dll`, `msvcp140_1.dll`, `msvcp140_2.dll`, `vcruntime140.dll`, `vcruntime140_1.dll` | OFFICIAL REDIST PREREQUISITE; independent recipient installation |
| Diagnostic app-local alternative: same5 unchanged official canonical files | REDISTRIBUTABLE APP-LOCAL CANONICAL, conditionally under Community terms; NOT chosen/shipped |
| Current unknown Microsoft CRT dependency | NONE |

Owner redistribution entitlement is supported by licensed Community2026
18.10.3 and the2026 Distributable List; release14.51.36247.0 files/installer are
validly Microsoft-signed and exact hashes are retained. The unchanged official
x64 installer has SHA256
`843068991daaa1f73ad9f6239bce4d0f6a07a51f18c37ea2a867e9beca71295c`.
Build-time entitlement, independently installed recipient runtime, conditional
app-local copying and third-party vendored filenames are distinct questions.
The chosen route does not exercise Mastixa redistribution of Microsoft code
or its installer. Recipients accept Microsoft terms when independently installing
it; Mastixa's AGPL license does not license that runtime. Protective downstream
assent/other Community distribution conditions would remain necessary for a
future bundled Microsoft installer or app-local route. No such route is implied.

Microsoft documents v140–v145 binary compatibility with sufficiently recent
runtime deployment;1243 imported names/ordinals on this exact remaining native
surface are exported by the qualified official runtime. This establishes the
narrow supported route, not a claim about undocumented older minimum versions.

## Validation and clean-machine assumption

Baseline, canonical app-local and canonical central frozen actual-main
diagnostics passed startup, Windows text events, PySide/shiboken, NumPy solve/
matrix/FFT, Shapely buffer/intersection/union, PROJ round-trip and actual Mastixa
parcel normalization, annual PDF generation and invoice QPixmap/PDF preview,
plus inert local updater staging/retry/SHA validation. No missing-DLL failures
or Qt messages occurred after diagnostic-harness repair. The initial harness
called NumPy.testing despite production exclusion of unittest; the repaired
driver uses NumPy.allclose. That failure was not a supplier/runtime defect.

Both normalized models load only five14.51.36247.0 canonical files: app-local
from `_internal/`, central exclusively from `Windows/System32`. Every loaded
CRT hash matches the qualified official Redist. None of the old14.40/14.44 or
hashed MSVCP files load. Startup and successive scientific/PDF/updater stages
record actual module paths; no VS/tooling/PATH module contamination was observed.
Bitdefender injected modules are identified separately as antivirus injection.

This is **controlled DLL-search validation plus dependency-resolution
simulation**, the allowed alternative to a pristine VM. PATH contains only
System32/Windows, CWD is an empty diagnostic directory, toolchain/Python/Qt
environment overrides are removed, and Windows search is restricted to System32
plus explicit bundle directories. The central artifact contains no CRT files;
141 CRT import edges resolve only to the five documented canonical runtime names.
An explicit absolute-System32 LoadLibraryEx probe independently verifies their
identity. A no-Redist model leaves those dependencies unsatisfied, so the installer
must reject that state. An Inno read-only probe compiled the production
prerequisite functions, checked old/minimum/newer versions and actual
Installed/version/System32 files, then aborted before installation.

No pristine VM was created and no new runtime was globally installed. This
result cannot replace later install/upgrade/artifact acceptance of the actual RC.
Full raw evidence/reproduction recipes are in `../WindowsB2NormalizationEvidence`.
The future RC still requires B1/B3/B4 closure and retained Bitdefender build-path
exclusion/indefinite owner-confirmation rules before the actual artifact build.

Primary references checked in this batch:

- [Microsoft binary compatibility](https://learn.microsoft.com/en-us/cpp/porting/binary-compat-2015-2017?view=msvc-170)
- [Microsoft CRT deployment/registry detection](https://learn.microsoft.com/en-us/cpp/windows/redistributing-visual-cpp-files?view=msvc-170)
- [Visual Studio2026 Distributable List](https://learn.microsoft.com/en-us/visualstudio/releases/2026/redistribution)
- [Community2026 terms](https://visualstudio.microsoft.com/license-terms/vs2026-ga-community/)
- [delvewheel repair and mangling options](https://github.com/adang1345/delvewheel)
