> Retained historical engineering record, sanitized for public review.
> Current status: [RELEASE_STATUS.md](RELEASE_STATUS.md). This record does not
> establish approval of the current source or a new binary release. Local-only
> receipt paths refer to privately retained evidence, absent from this snapshot.

> Current legal gate2026-10-08: B1-LEGAL/B4-LEGAL PASS; B1-AUDIT/B4-REPRO INCOMPLETE (non-blocking); B3-LEGAL BLOCKED.
> Prior private-CI/bit-identical/full-rebuild prerequisites are superseded by WINDOWS_RELEASE_GATE_POLICY.md.
> Required matching source/controlling scripts/replacement rights and future public source access remain mandatory.
> Exact review: WINDOWS_B3_LEGAL_CLOSURE.md. No RC build/preflight authorized by this note.

> Current2026-10-08 upstream receipt review: B1/B4 BLOCKED for requested exact
> correspondence; unavailable CI logs are not an independent legal requirement.
> B3 rights/terms basis remains unresolved; B2/B5 PASS RETAINED.
> See WINDOWS_UPSTREAM_RECEIPT_CLOSURE.md, windows-upstream-receipt-closure.json,
> WINDOWS_DEPENDENCY_REBUILD.md and windows-release-retention-manifest.json.
> Older producer-log/full-rebuild blocker wording below is superseded.

# QtPdf recipient rebuild instructions — 2026-10-08

This is a functional recipient recipe, not a demonstrated bit-identical producer
rebuild. B1/B4 remain BLOCKED. The executed narrow stage below generates real
QPdfDocument metadata; no newly rebuilt Qt6Pdf DLL was produced or loaded.
The prior identifiable modified-library startup/PDF/preview PASS is retained.

## Sources and patches

Use the complete official `qtwebengine-everywhere-src-6.11.2.tar.xz`, SHA256
`6101c1aa00ff933d1b65ee5d167f76e8d71b9ac5b378b0111277723ebda7c163`.
QtWebEngine commit: `a33fa2a897e5ee58e385b3f88dc247d99fca56db`.
QtPdf source is `src/pdf`, image plugin `src/pdf/plugins/imageformats/pdf`.
Nested Qt Chromium commit: `5170777d28bee1ce92cc693a0dbf2ad01492e5cf`.
Its Chromium DEPS pins PDFium `1afaa1a380fcd06cec420f3e5b6ec1d2ccb920dc`.
The final Qt PDFium tree is `a73e60360d4a1b21df9b41b59d46db1ab489d42a`.

Use that final release source directly. It already contains Qt integration and
backports; do not apply the retained comparison patch on top. The isolated
baseline comparison found 2,880 identical members, 54 changed members and 1,620
upstream members omitted by the Qt snapshot. Exact changed-source hashes, full
text delta and source history are retained in WindowsProducerRebuildEvidence.
Omitted upstream members are not all patches or compiled dependencies. The delta
captures final source differences, not proof of the producer's patch execution.
Qt's `tools/scripts/version_resolver.py` describes exporting snapshot commits via
git format-patch; a release tarball has final contents without the Git history.

## Functional build prerequisites

Use an isolated short writable directory, a complete x64 Qt6.11.2 MSVC2022
development SDK (headers, private headers, import libraries, CMake BuildInternals,
moc and other host tools), and the complete QtWebEngine archive above. The
retained Qtbase SDK/source correspondence is documented separately. A PySide
runtime wheel alone is not this development SDK. The selectively extracted SDK
used by the diagnostic is not a complete link environment.

Open an x64 VS2022 developer shell. Qt's Windows GN helper explicitly selects
visual_studio_version=2022; use the matching compiler19.44.35227.0 where available
for the closest retained SDK correspondence. CMake3.30.5 and Ninja1.10.2 were
retained for the SDK producer; use compatible versions for the functional build.
Windows SDK10.0.26100.0 is a chosen functional prerequisite, not an established
QtPdf producer SDK receipt. Supply Python3.8+ with html5lib; retain exact Python,
package and tool hashes. The host's VS2026 compiler19.51 is not a verified
substitute for the QtPdf producer toolchain. No VS installation was changed.

Example PowerShell sequence inside that developer shell, after provisioning
those prerequisites and verifying source/tool hashes:

```powershell
$taskRoot = 'C:\MastixaQtPdfRebuild'
$taskSdk = 'C:\Qt\6.11.2\msvc2022_64'
$taskPython = 'C:\MastixaQtPdfRebuild\python\python.exe'
$taskArchive = 'C:\MastixaQtPdfRebuild\inputs\qtwebengine-everywhere-src-6.11.2.tar.xz'
if ((Get-FileHash -LiteralPath $taskArchive -Algorithm SHA256).Hash.ToLower() -ne '6101c1aa00ff933d1b65ee5d167f76e8d71b9ac5b378b0111277723ebda7c163') { throw 'Source mismatch' }
New-Item -ItemType Directory -Path "$taskRoot\source" -Force | Out-Null
tar.exe -xf $taskArchive -C "$taskRoot\source"
if ($LASTEXITCODE) { throw 'Extraction failed' }
$taskSource = "$taskRoot\source\qtwebengine-everywhere-src-6.11.2"
$taskBuild = "$taskRoot\build"
$env:PATH = "$taskSdk\bin;$env:PATH"
cmake -S $taskSource -B $taskBuild -G Ninja `
  "-DCMAKE_PREFIX_PATH=$taskSdk" "-DPython3_EXECUTABLE=$taskPython" `
  -DCMAKE_BUILD_TYPE=Release -DQT_BUILD_TESTS=OFF -DQT_BUILD_EXAMPLES=OFF `
  -DFEATURE_qtwebengine_build=OFF -DFEATURE_qtpdf_build=ON `
  -DFEATURE_qtpdf_widgets_build=OFF -DFEATURE_qtpdf_quick_build=OFF `
  -DFEATURE_pdf_v8=OFF -DFEATURE_pdf_xfa=OFF
if ($LASTEXITCODE) { throw 'Configure failed; retain its diagnostics' }
cmake --build $taskBuild --target Pdf QPdfPlugin --parallel 2
if ($LASTEXITCODE) { throw 'Build failed; retain its diagnostics' }
Get-ChildItem -LiteralPath $taskBuild -Recurse -File |
  Where-Object Name -in 'Qt6Pdf.dll','qpdf.dll','args.gn','CMakeCache.txt','build.ninja' |
  ForEach-Object { Get-FileHash -LiteralPath $_.FullName -Algorithm SHA256 }
```

These feature choices define a minimal functional PDF build for Mastixa invoice
preview; they are not claimed as upstream wheel build args. Qt source constructs
GN arguments in `src/pdf/CMakeLists.txt` and `cmake/QtToolchainHelpers.cmake`,
then generates the QtPdf static archive from `//third_party/pdfium` and links it
into Qt6Pdf. Keep all emitted args.gn, toolchain files, commands, linker responses,
generated source and hashes. If CMake reports an unmet prerequisite, supply the
named prerequisite rather than silently change the recipe. The full configure,
compile and DLL-load sequence above has not been demonstrated in this batch.

## Executed stage and replacement

`../WindowsProducerRebuildEvidence/run_pdf_moc.py` runs the retained Qt6.11.2 SDK
moc on the actual `src/pdf/qpdfdocument.h` twice. Both exits were0 and outputs
had SHA256 `deede3ee28fb8d3ea42feea2e1df06bd838d7f02ada47497a7de59d19b2f857d`.
The isolated include tree contains source headers plus an export header and
empty feature-config stub for this metadata-only stage. These are explicit
diagnostic scaffolding, not recovered producer-generated headers. This proves
a meaningful QtPdf generator stage; it does not compile PDFium or rebuild a DLL.

For the companion binding stage, `run_generator.py` and binding-regeneration.json
retain exact Shiboken6.11.2 commands, SDK/typesystem input paths, tool hashes and
18 matching generated C++/header outputs (9 wrappers +9 headers) across two runs.
The tool uses Clang20, MSVC emulation and an explicit builtin offsetof parser
setting; the setting fixes the first retained diagnostic failure. It is not a
producer-option receipt. A timing log differs; generated source does not.
Official generated producer C++ outputs are absent from the exact source archive,
so no binary correspondence or bit-identical regeneration is claimed.

After a successful full functional build, close Mastixa and copy the coherent
Qt6Pdf.dll/qpdf.dll pair into an isolated writable recipient copy at
`_internal/PySide6/Qt6Pdf.dll` and `plugins/imageformats/qpdf.dll`. Preserve ABI,
exports and compatible dependent Qt DLLs. Run the retained replacement probe with
a synthetic QA profile and verify GetModuleHandle/GetModuleFileName path, DLL
SHA, startup, report PDF export and invoice preview. See
WINDOWS_LIBRARY_REPLACEMENT.md for the exact already-tested modified DLL and
explicit update/repair backup/reapply procedure. No rebuilt DLL load is claimed.

## Producer reproduction still missing

The shipped Qt6Pdf SHA is
`6fc87c84a723b05a0a3d7dce87083d25d23b1558e8806ff1cc7952bb9c5c9779`;
qpdf SHA is `541350d584d990b8dcccb6726a4cb2169b901b90b6221273f813a13256570705`.
Missing: exact producer job-to-artifact hash chain, executed GN args/features,
compiler/linker/SDK/GN identities, build cache/responses and any producer-only
patches beyond the final released source. Binding production also lacks exact
header/config/options/output receipts. Matching GEOS build/patch/config materials
remain required by B4. A compatible functional recipe is useful but does not
close these exact-source/build conditions. Do not run final preflight or build RC.
