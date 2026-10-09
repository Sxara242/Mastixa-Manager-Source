> Retained historical engineering record, sanitized for public review.
> Current status: [RELEASE_STATUS.md](RELEASE_STATUS.md). This record does not
> establish approval of the current source or a new binary release. Local-only
> receipt paths refer to privately retained evidence, absent from this snapshot.

# Windows Mesa/native B5 closure — 2026-10-07

**B5 PASS — FINAL B1–B4 CLOSURE REMAINS.** RELEASE-INFRA / DESKTOP, Windows
x64. Mesa/native disposition: **EXCLUDE**, with **SAFE TO EXCLUDE** established
for the current raster Widgets application. This is not security acceptance of
the legacy libraries. OpenSSL qualification is reused unchanged. B1–B4 remain
BLOCKED and both readiness flags remain false. No final RC or installer.

## Exact before-state identity and supplier

Only one shipping native file contains both projects. There is no standalone
LLVM DLL, separate llvmpipe DLL, ANGLE payload or tooling Mesa copy in the
retained 115-file shipping set.

| Field | Verified value |
| --- | --- |
| Filename / planned shipping path | `opengl32sw.dll` / `_internal/PySide6/opengl32sw.dll` |
| Actual retained frozen path | `<WORKSPACE>/WindowsOpenSslPromotionEvidence/dist/MastixaPromotedTlsDiagnostic/_internal/PySide6/opengl32sw.dll` |
| Architecture / size | PE AMD64 `0x8664`; 20,639,544 bytes |
| File version resource | Absent; do not manufacture a PE FileVersion |
| Embedded upstream identities | `Mesa 11.2.2`, `llvm-mc (based on LLVM 3.6.2)`, `llvmpipe` |
| SHA-256 | `34b444c016289b560662ff896deceb7f4b2c0723aed3d319ae167c9186ce42b3` |
| Parent package | `pyside6_essentials-6.11.2-cp310-abi3-win_amd64.whl`, member `PySide6/opengl32sw.dll` |
| Wheel SHA-256 | `c8a29def77032773a30879f7f24415b5395ad08592d147c170824ef4c735dfc1` |
| Collection | PyInstaller 6.22.3 QtGui helper `collect_extra_binaries()` explicitly collects `opengl32sw.dll` if available |
| Native reverse imports | Zero import/delay-import edges to this DLL in all 115 retained emitted native inputs |
| Runtime consumer | Windows Qt platform plugin WGL loader; dynamically discoverable on an OpenGL-context request |

Fresh wheel member/RECORD/frozen hash equality is in sibling
`WindowsMesaNativeEvidence/identity.json`. Previous official wheel qualification
is reused. All eight PE sections match the original Qt-hosted 11.2.2 prebuilt
and its signed variant; complete file hashes differ because signing wrappers
differ. Retained supplier archive hash/section receipts are preserved in
`windows-mesa-provenance.json`. This proves origin, not a complete static
dependency, patch, compiler or security receipt. Mesa is **not PATH/tooling
contamination**; its automatic inclusion was an unnecessary packaging input.

Supplier: [Qt official llvmpipe prebuilt directory](https://download.qt.io/development_releases/prebuilt/llvmpipe/windows/).
The exact wheel archive remains locally retained in WindowsBlockerClosureEvidence.
No wheel, Qt/PySide version, build venv or supplier binary was modified.

## Runtime role and necessity

The exact retained qtbase 6.11.2 source was inspected, not just filenames.
`QWindowsIntegration::staticOpenGLContext()` initializes lazily;
`QWindowsStaticOpenGLContext::doCreate()` selects system or software OpenGL;
`QWindowsOpengl32DLL::init()` uses system `opengl32` or software `opengl32sw`,
with `QT_OPENGL_DLL` overriding the requested library. `QT_OPENGL=software`,
AA_UseSoftwareOpenGL, a failed desktop implementation or an applicable driver
buglist can select the Mesa fallback **when an OpenGL context is requested**.
Qt6 ANGLE is not this DLL's role. Source extracts and native import/delay-import
graph are retained in WindowsMesaNativeEvidence.

Mastixa's Windows source has no OpenGL/Quick/QML consumer. The inspected
application routes use raster QWidget/QPainter/QImage/QPixmap/QPrinter and the
bundle-local qpdf/Qt6Pdf image plugin. Software raster painting is independent
of software **OpenGL**. No Mesa requirement was established for PDF/image,
report export, headless raster rendering, themes or updater. The application's
ordinary window is `RasterSurface`; QImage's paint engine is `Raster`.
This interpretation is supported by [Qt graphics documentation](https://doc.qt.io/qt-6.11/windows-graphics.html)
and [Qt paint-device documentation](https://doc.qt.io/qt-6.11/paintsystem-devices.html).

Actual module snapshots cover startup, report export, invoice PDF preview,
Dark, Light and updater. The baseline does **not load Mesa/LLVM** at any of
these stages. A deliberately added diagnostic QOpenGLContext with software
OpenGL does load the exact bundle-local Mesa DLL, proving the conditional path
is real. It is not an application feature or a required supported-user route.

| Frozen synthetic run | Required Mastixa routes | Added diagnostic GL request |
| --- | --- | --- |
| `normal-baseline.json`, original DLL present | PASS; Mesa absent from every normal stage | None |
| `software-baseline.json`, software requested | PASS; Mesa absent before context request | Context/current PASS; Mesa loads bundle-local |
| `exclusion-normal.json`, isolated DLL exclusion | PASS; zero Qt messages | None |
| `exclusion-software.json` | PASS; normal raster stages intact | Missing software library reported; Qt falls back to system OpenGL, context/current PASS |
| `exclusion-desktop.json` | PASS; zero Qt messages | System OpenGL context/current PASS; no Mesa |
| `exclusion-no-GL.json`, nonexistent explicit GL library | PASS even with OpenGL unavailable | Expected failed context/current; injected failure messages retained |
| `guarded-normal.json`, production policy/guards | PASS; zero Qt messages | None |
| `guarded-no-GL.json`, production policy/guards | PASS even with OpenGL unavailable | Expected failed context/current |

The unavailable-GL experiment demonstrates that required routes need neither
Mesa nor a working hardware OpenGL driver; it does not promise a future
QOpenGLWidget will work on such systems. This is one native Windows host with
synthetic profiles, not a multi-GPU/VM certification. Future graphics consumers
require fresh qualification; the regression detects such source additions.

## Exclusion, security and source disposition

`qt_exclusions.py` removes the exact `opengl32sw.dll` basename in either TOC
destination or source, case-insensitively, for binaries and data. No other Mesa
or LLVM filename is invented or removed. `mesa_policy.py` rejects reappearance
after Analysis and after COLLECT, including relocated names and the three exact
known wheel/supplier signing-variant hashes under DLL/PYD aliases. The release
validator repeats the bundle guard before installer collection. Existing
restricted supplier discovery remains; wheel or tooling copies with this name
cannot reenter. These are packaging checks, not installed-library restrictions.

Mesa 11.2.2 is a [2016 release](https://docs.mesa3d.org/relnotes/11.2.2.html);
[LLVM 3.6.2](https://releases.llvm.org/3.6.2/docs/ReleaseNotes.html) is also a
legacy upstream release. Mesa's [current release calendar](https://docs.mesa3d.org/release-calendar.html)
does not list this branch. Supplier maintenance, patches, exact static build
and applicable security closure remain unqualified for the old bytes. No
zero-CVE claim or fallback-only exemption is made. The selected classification
is **EXCLUDE**: both codebases are absent from the guarded shipping output and
there is no remaining reachable shipped Mesa/LLVM code requiring an update.
No broader Qt/PySide migration or unofficial graphics replacement was needed.

The previous candidate notices identify Mesa MIT-style and LLVM UIUC/NCSA plus
third-party terms. Exact supplier/static notice closure was incomplete and
would still be required if retained. There is now no Mesa/LLVM binary to
redistribute and no corresponding-source/replacement obligation for that
removed binary in this distribution. Existing source/legal receipts and base
legal texts are preserved as historical/reference material; their presence
does not imply code ships or qualify the legacy binary. Do not delete evidence
or source retention. All unrelated B1–B4 obligations remain.

## Validation and next action

Nine focused tests and **301 targeted checks PASS**, zero failures/errors/skips, Qt messages and
ResourceWarnings. They cover exact TOC exclusion, required DLL retention,
named/aliased reappearance, release validation, future graphics consumers and
actual PDF export/preview. Frozen checks cover actual main.py startup, normal
text input, annual report PDF export, invoice QPixmap preview, basic widgets,
Light/Dark screenshots, offline staging and local synthetic updater retry/SHA/
mismatch preservation. The updater uses an injected loopback HTTP transport
behind synthetic HTTPS metadata; no TLS advisory/HTTPS requalification was
rerun, no inert bytes executed, and no public updater E2E claim is made.

All snapshots allow only bundle-local dependencies and Windows system modules,
with explicitly recorded installed Bitdefender injection as an environmental
exception. Antivirus injection is not a collected supplier or PATH dependency.
All required qpdf/platform modules load bundle-local; no global tool/PATH Mesa
or application dependency loads. Normal runs are free of DLL-load errors;
only deliberately injected diagnostic OpenGL failures produce expected warnings.

Only one native record and its SBOM component/composition reference are removed:
115 → **114 native**, 151 → **150 SBOM components**. Pure modules 1,216,
17 package families, seven Qt modules and 21 plugins remain. All 114 native
input hashes match the qualified promoted bundle. Project notice/source-plan
and legal-index data hashes are updated only where affected. Manifest/SBOM delta,
official CycloneDX 1.6 schema, independent deterministic generation, packaging
guards and `git diff --check` are recorded in `verification.json` and related
files in WindowsMesaNativeEvidence. Earlier diagnostic EXE hashes are not RC
SBOM components or a final reproducible RC build claim.

**B5 PASS.** CPython/OpenSSL and Qt/OpenSSL pins/evidence are unchanged and
reused. B1 producer Qt/PDFium notices/build receipts; B2 Microsoft applicable
grants/recipient/release-status evidence; B3 remaining CRS/EPSG mapping/terms;
B4 matching nested sources/build/replacement/application archive remain blocked.
Both readiness flags remain false. Exact next step: a separately authorized
final B1–B4 materials closure, reusing current wheel/TLS/Mesa evidence when
inputs are unchanged. Do not build the final RC in this batch.

Approved worktree/HEAD and all protected/unrelated dirty work are preserved;
Git: **52 tracked modified / 264 untracked / 0 staged**; protected original
**32 modified / 32 untracked / 0 staged**, with identical whole content/status.
Exact before/after hashes are in preservation-final.json.
No reset, clean, revert, discard, commit, push, tag, publication or upload.
