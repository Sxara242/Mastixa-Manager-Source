> Retained historical engineering record, sanitized for public review.
> Current status: [RELEASE_STATUS.md](RELEASE_STATUS.md). This record does not
> establish approval of the current source or a new binary release. Local-only
> receipt paths refer to privately retained evidence, absent from this snapshot.

> Current legal gate2026-10-08: B1-LEGAL/B4-LEGAL PASS; B1-AUDIT/B4-REPRO INCOMPLETE (non-blocking); B3-LEGAL BLOCKED.
> Prior private-CI/bit-identical/full-rebuild prerequisites are superseded by WINDOWS_RELEASE_GATE_POLICY.md.
> Required matching source/controlling scripts/replacement rights and future public source access remain mandatory.
> Exact review: WINDOWS_B3_LEGAL_CLOSURE.md. No RC build/preflight authorized by this note.

# Windows dependency rebuild supplement — 2026-10-08

RELEASE-INFRA / DESKTOP. These are recipient process instructions, not a promise
of bit-identical upstream wheels. The existing 757-file Mastixa source candidate
remains immutable. Use the source/material retention manifest and the supplement
alongside it. No full dependency rebuild was run in this batch.

## PySide / Shiboken

Use the complete official `pyside-setup-everywhere-src-6.11.2.tar.xz`, SHA256
`cba47efbaad1bedd529725cbc14e21f156c7a19366f07b3edfbb076ffd7afdf8`.
It contains generator source `sources/shiboken6`, PySide typesystems, umbrella
headers, CMake generation rules, `setup.py`, `build_scripts` and `coin` scripts.
The generator wheel 6.11.2 and its exact hash are already retained. Generated
producer wrappers are absent from the source release. Automatically regenerable
outputs need not be delivered separately under GPLv3 section1; the necessary
source inputs and controlling scripts must be delivered.

The official `coin/instructions_utils.py` chooses Python3.10.0 on Windows and
calls setup.py build with `--standalone --unity --build-tests --log-level=verbose
--limited-api=yes --shorter-paths`, qtpaths from ENV_INSTALL_DIR and a CI package
timestamp. This is a published producer recipe, not a recovered executed CI
environment. CMake/headers/generation options are controlled by the archived
source scripts. Qt release/SDK configuration and optional environment values
still have to correspond to the intended rebuild. Do not describe the retained
18 QtPrintSupport diagnostic outputs as the entire binding build.

For a functional recipient build, provision x64 MSVC, a complete compatible
Qt6.11.2 development SDK, matching Clang/libclang as specified by that source's
build documentation, Python with limited API support, CMake/Ninja and the
archive's requirements. In a dedicated developer shell, after verified source
extraction, a scoped build command is:

```powershell
$taskSdk = 'C:\Qt\6.11.2\msvc2022_64'
$taskPython = 'C:\MastixaBindingRebuild\python\python.exe'
& $taskPython setup.py build --standalone --unity --limited-api=yes `
  --shorter-paths --ignore-git --module-subset=Core,Gui,Widgets,Network,PrintSupport `
  "--qtpaths=$taskSdk\bin\qtpaths.exe" --parallel=2
if ($LASTEXITCODE) { throw 'Binding build failed; retain diagnostics' }
```

Run in the extracted pyside setup root. Preserve emitted generator commands,
typesystem/header hashes, compiler options and the coherent PySide/Shiboken
runtime/wrapper set. Do not copy an isolated .pyd across incompatible runtimes.
Replace the corresponding files under `_internal/PySide6` and
`_internal/shiboken6` only in a writable recipient copy; verify loaded paths and
the functions using each wrapper. The existing diagnostic proved a generator
stage, not this complete build or loading a rebuilt binding set.

## GEOS / Shapely

Exact inputs:

- GEOS3.13.1 source, `geos-3.13.1.tar.bz2`, SHA256
  `df2c50503295f325e7c8d7b783aca8ba4773919cde984193850cf9e361dfd28c`.
- Shapely2.1.2 sdist SHA256
  `2ed4ecb28320a433db18a5bf029986aa8afcfd740745e78847e330d5d94922a9`.
- Producer commit `5fb639d1056888d135fe56bfaf750c9648addeec`, full retained archive
  SHA256 `67973d5a0215eece7a2b0b7406a91a4172189325cb05d1c0fc11a74d96086dff`.
  `ci/install_geos.cmd` and `.github/workflows/release.yml` are included.

The recipe selects Windows2022 AMD64, x64 MSVC, cibuildwheel3.2.0, GEOS3.13.1,
Ninja, Release and BUILD_SHARED_LIBS=ON. It applies no GEOS source patch command.
It downloads the original source, compiles and installs it, builds Shapely with
GEOS_INCLUDE_PATH/GEOS_LIBRARY_PATH, then repairs the wheel with delvewheel.
The official wheel loader records delvewheel1.11.1. Compiler/CMake/Ninja and
several pip dependencies were not version pinned; their historical versions are
audit/reproducibility information, not evidence of a missing GEOS source patch.

From an isolated x64 developer shell with compatible MSVC/CMake/Ninja:

```powershell
$taskRoot = 'C:\MastixaGeosRebuild'
$taskInstall = "$taskRoot\geos-install"
cmake -S "$taskRoot\geos-3.13.1" -B "$taskRoot\geos-build" -G Ninja `
  -DCMAKE_BUILD_TYPE=Release -DBUILD_SHARED_LIBS=ON `
  "-DCMAKE_INSTALL_PREFIX=$taskInstall"
if ($LASTEXITCODE) { throw 'GEOS configure failed' }
cmake --build "$taskRoot\geos-build" --parallel 2
if ($LASTEXITCODE) { throw 'GEOS build failed' }
cmake --install "$taskRoot\geos-build"
if ($LASTEXITCODE) { throw 'GEOS installation failed' }
$env:GEOS_INCLUDE_PATH = "$taskInstall\include"
$env:GEOS_LIBRARY_PATH = "$taskInstall\lib"
# Use an isolated CPython3.14 x64 environment with Cython, NumPy, setuptools,
# wheel, pip and delvewheel1.11.1; record chosen compatible versions/hashes.
python -m pip wheel --no-deps --no-build-isolation `
  "$taskRoot\shapely-2.1.2" -w "$taskRoot\wheel-unrepaired"
if ($LASTEXITCODE) { throw 'Shapely build failed' }
Get-ChildItem -LiteralPath "$taskRoot\wheel-unrepaired" -Filter '*.whl' |
  ForEach-Object {
    python -m delvewheel repair --add-path "$taskInstall\bin" `
      -w "$taskRoot\wheel-repaired" $_.FullName
    if ($LASTEXITCODE) { throw 'Wheel repair failed' }
  }
```

For source modifications, rebuild and replace a coherent Shapely extension,
loader and GEOS DLL set. Delvewheel generates interdependent mangled DLL names;
renaming only geos.dll will not fix the imports. Extract/install the repaired
wheel into a separate recipient staging directory and copy its `shapely` and
`shapely.libs` directories to the matching `_internal` directories of a writable
Mastixa copy, preserving all new names/imports. Windows directory case is
insensitive; the shipping manifest uses `Shapely.libs`.

Retained B2 normalization records map original GEOS wheel hashes to current
shipping hashes. They change a hashed MSVCP import to independently installed
msvcp140.dll and the PE checksum, not GEOS source code. A newly repaired wheel
needs compatible canonical CRT imports. The publisher's locked production
`crt_policy.py` rejects unexpected hashes; do not loosen it for a recipient
build or rerun B2. No runtime guard prohibits a compatible recipient DLL set.
If the new wheel carries app-local CRTs, use canonical independently installed
CRT linkage in the isolated build instead of copying them into the application.

Verify the actual loaded geos/geos_c paths and hashes, `geos_version_string`,
geometry operations and Mastixa's GIS path using a synthetic profile. No GEOS
rebuild/load test was performed here. The license requires usable source and
dynamic replacement; it does not require the publisher to rebuild every covered
library or reproduce the historical compiler hash. Keep LGPL2.1 and Shapely BSD
notices and document changes. Update/repair backup/reapply behavior is described
in WINDOWS_LIBRARY_REPLACEMENT.md.

## QtPdf and retention

Use WINDOWS_QTPDF_REBUILD.md for the existing full source, patched PDFium,
functional build commands and already-tested replacement path. Use
windows-release-retention-manifest.json for the exact 757-file base, versioned
source receipts, controlling scripts and source supplement. Future installer
hash/source binding is recorded only after a separately authorized RC build;
its absence before that build is not a missing upstream CI receipt.
