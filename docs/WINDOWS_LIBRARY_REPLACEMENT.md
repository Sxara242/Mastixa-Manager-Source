> Retained historical engineering record, sanitized for public review.
> Current status: [RELEASE_STATUS.md](RELEASE_STATUS.md). This record does not
> establish approval of the current source or a new binary release. Local-only
> receipt paths refer to privately retained evidence, absent from this snapshot.

> Current legal gate2026-10-08: B1-LEGAL/B4-LEGAL PASS; B1-AUDIT/B4-REPRO INCOMPLETE (non-blocking); B3-LEGAL BLOCKED.
> Prior private-CI/bit-identical/full-rebuild prerequisites are superseded by WINDOWS_RELEASE_GATE_POLICY.md.
> Required matching source/controlling scripts/replacement rights and future public source access remain mandatory.
> Exact review: WINDOWS_B3_LEGAL_CLOSURE.md. No RC build/preflight authorized by this note.

> Historical upstream receipt review, superseded above: B1/B4 BLOCKED for requested exact
> correspondence; unavailable CI logs are not an independent legal requirement.
> B3 rights/terms basis remains unresolved; B2/B5 PASS RETAINED.
> See WINDOWS_UPSTREAM_RECEIPT_CLOSURE.md, windows-upstream-receipt-closure.json,
> WINDOWS_DEPENDENCY_REBUILD.md and windows-release-retention-manifest.json.
> Older producer-log/full-rebuild blocker wording below is superseded.

> New functional rebuild prerequisites/commands and executed QtPdf MOC stage: WINDOWS_QTPDF_REBUILD.md. Practical modified-DLL loading below remains PASS RETAINED; full rebuilt-DLL loading is not claimed.

# Recipient library replacement β€” narrow evidence 2026-10-08

The owner-authorized benign identifiable QtPdf variant test PASSED. The isolated
recipient copy of the retained current-policy onedir package loaded modified
`_internal/PySide6/Qt6Pdf.dll` with a new RT_RCDATA resource62123. Original SHA256
`6fc87c84a723b05a0a3d7dce87083d25d23b1558e8806ff1cc7952bb9c5c9779`;
modified SHA256 `54a204d34beea013a62bed004cfe71f535eb671c774fbbdf4a1402f6270ebabf`.
The non-resource PE sections and export names were identical. This is a controlled
recipient modification, not a rebuilt library or producer/source correspondence
claim. Original wheel/supplier and retained diagnostic bytes remain unchanged.

The B4-only diagnostic executable reused the retained PYZ/bootstrap and current
main.py. No Analysis, full audit, B2/B5 test suite or final RC build was run.
Actual visible startup, report PDF export and invoice QPixmap/qpdf preview PASS.
GetModuleHandle/GetModuleFileName confirmed the exact changed QtPdf path/hash and
the bundle-local qpdf plugin. One printer CreateDC warning was recorded; PDF output
and preview still passed. Two initial harness API mistakes were corrected and
their failed evidence retained; no application change was necessary.

For an end user:

1. Close Mastixa. Copy the entire onedir application to a writable test directory;
   keep the original copy and your replacement libraries backed up. Use a new
   synthetic QA profile for checks, never your production database.
2. Replace compatible x64 Qt DLLs/plugins in `_internal/PySide6` (the PDF plugin is
   `plugins/imageformats/qpdf.dll`); PySide wrappers/runtime use this directory,
   Shiboken uses `_internal/shiboken6`. GEOS uses `_internal/Shapely.libs` with the
   exact wheel-mangled names and matching imports. Preserve Python limited-API,
   Qt6.11 ABI, all required exports and the coherent dependent set.
3. For the demonstrated variant, use the exact retained `prepare_replacement.py`
   recipe to add a harmless RT_RCDATA marker to a COPY of Qt6Pdf.dll with Win32
   BeginUpdateResource/UpdateResource/EndUpdateResource. This changes its bytes
   without changing compiled code/import/export sections. Rebuild from the exact
   upstream source/patch/config/toolchain set for substantive library changes;
   matching release source/necessary scripts are retained. Exact private producer
   configuration and full/bit-identical reproduction remain audit follow-up;
   B4-LEGAL is PASS for prebuild preparation. Validate each substantive rebuilt
   set before using it; the retained probe demonstrates the resource variant only.
4. Launch from the writable copy. Verify actual loaded DLL paths/hashes, visible
   startup, text input and the functions using the changed libraries: PDF export
   and invoice preview for QtPdf; GIS geometry/transforms for GEOS/PROJ. The
   retained narrow probe validates QtPdf only; it does not claim rebuilt binding
   or GEOS qualification. Remove the test copy or return to the original to undo.
5. Explicit repair/update installs overwrite matching program files: current Inno
   `[Files]` recursively copies with `ignoreversion`; the updater verifies the
   downloaded INSTALLER's SHA, not installed LGPL DLLs. Back up replacements,
   install an update explicitly, then reapply an ABI-compatible set for that new
   release, or keep a separate versioned writable copy. Do not apply stale DLLs
   blindly to a changed Qt/Python ABI. No automatic installed-library self-healing
   or runtime DLL hash/signature guard was found in the reviewed startup/updater.

Build-time trusted-supplier/TLS/CRT/Mesa/legal checks remain intact. They qualify
the publisher's inputs/output and are not normal recipient startup guards. No
production guard, installer, updater or native packaging path was changed here.
Recipient debugging/reverse engineering of covered-library modifications remains
permitted by the applicable LGPL route. Suitable dynamic linking avoids an
automatic blanket application-object-file obligation; complete corresponding
library source and necessary build/installation information remain required.

Raw experiment: `../WindowsNarrowClosureEvidence/variant.json`,
`replacement-result.json`, `replacement-launch.json`, `prepare_replacement.py`,
`replacement_driver.py`, `ReplacementProbe.spec`. These are internal evidence,
not public download links. The eventual source delivery must include the curated
recipe/probe and matching rebuild materials; do not ship private profile/log data.
