> Retained historical engineering record, sanitized for public review.
> Current status: [RELEASE_STATUS.md](RELEASE_STATUS.md). This record does not
> establish approval of the current source or a new binary release. Local-only
> receipt paths refer to privately retained evidence, absent from this snapshot.

# OpenSSL supplier qualification and promotion — 2026-10-07

**BLOCKED BEFORE RC BUILD. B5 BLOCKED solely for the retained Mesa/native maintenance/security/build qualification gap. The OpenSSL supplier/promotion/frozen subgate is PASS.** B1-B4 statuses remain blocked; only the two CRT input records in B2 change; neither native notices nor corresponding-source readiness is true. RELEASE-INFRA / DESKTOP, Windows x64. No final RC, installer, commit, push, tag, upload or publication.

| Stack | Before -> promoted release input | Result |
| --- | --- | --- |
| Python | CPython 3.14.6 / OpenSSL 3.5.7 -> complete PSF CPython 3.14.8 / OpenSSL 3.5.9 | ACCEPTABLE FOR RC for OpenSSL; coherent runtime + unchanged 23-wheel lock qualified |
| Qt | Qt/PySide6 6.11.2 + accidental Poppler OpenSSL 3.6.4 -> same Qt/PySide + FireDaemon OpenSSL 3.5.9 LTS | ACCEPTABLE FOR RC for OpenSSL; 305 exported resolver symbols and frozen runtime qualified |

The supported patched3.5.9 LTS replacement fixes the reviewed3.6.4 issues; semantic minor numbering is not a Qt dependency. No Qt/PySide update, Qt rebuild or commercial Qt is required for this TLS change. Mesa remains a separate existing blocker; this batch does not transfer it to another gate or certify it.

## Supplier and ABI evidence

Priority channels checked: Qt official x64 tool feed still offers3.0.16-1 and is rejected as unpatched/unsupported for this task; qualified PySide6 Essentials/Addons6.11.2 wheels have the Qt TLS plugin but no OpenSSL DLL pair; official upstream Windows installer is testing4.0.1, the wrong major ABI. Upstream native `VC-WIN64A`/HYBRIDCRT source build is supported but local MSVC/Perl/NASM/nmake tools were not found in PATH or standard install locations. No toolchain was installed. Shining Light's supplier/hash channels were considered, not downloaded or adopted; supplier integration/payment/build-receipt questions were unnecessary once the documented FireDaemon route qualified.

The [original FireDaemon supplier](https://kb.firedaemon.com/support/solutions/articles/4000121705) explicitly permits free use/redistribution and integration into any Windows application. OpenSSL's binary wiki lists it but explicitly does not endorse third-party products. Acceptance here comes from exact signed supplier bytes, source/build/configuration receipts, ABI/export evidence and actual Qt 6.11.2 frozen qualification; it is not an invented Qt or OpenSSL Project endorsement.

Qt 6.11.2 `qopensslbackend.dll` and Qt6Network match the retained wheel. PE machine0x8664; no static OpenSSL DLL import: Qt dynamically resolves them. Actual runtime build string is OpenSSL 3.5.4. Exact source loader uses major3, filenames `libssl-3-x64.dll` and `libcrypto-3-x64.dll`, and Windows x64 ABI. All 305 `RESOLVEFUNC` names present in this binary are exported by the candidate; no missing symbol. The pair's libssl imports its matching libcrypto-3-x64.dll. Source, PE imports/exports and hashes are in `WindowsOpenSslPromotionEvidence/qt-abi.json`. OpenSSL's major-version compatibility policy plus successful symbol/behavior checks support this3.5.9 swap; patch compatibility was tested, not presumed.

Supplier ZIP: https://download.firedaemon.com/FireDaemon-OpenSSL/openssl-3.5.9.zip
SHA-256: `76da391395be029b44794857b9ff380255e02a0960a98314cd3f6a6816d82696`. Both DLL Authenticode signatures Valid / FireDaemon Technologies Limited; native file versions3.5.9. Only the two unmodified x64 DLLs enter the bundle. No x86/ARM64 binary, installer, openssl.exe, sample project, engine, legacy/FIPS provider or supplier configuration ships.

Source: https://github.com/openssl/openssl/releases/download/openssl-3.5.9/openssl-3.5.9.tar.gz
SHA-256: `603f5602e2eef00d77fbd429d34dcd5822bb301757a1bc9cdb24c670f1eb859a`; exact tag commit `45e844fa2a14ec92d146bd8f5778ac130b6625fb` matches supplier version.txt `openssl-3.5.9-0-g45e844fa2a`. Supplier states direct upstream source; retained build script has no patch step. Receipt https://download.firedaemon.com/FireDaemon-OpenSSL/mkopenssl.zip SHA-256 `f6fca4e764d328b51eb495068450bd647d873b6c69bc768db02a372d8b046d25`. Retained flags: VC-WIN64A-HYBRIDCRT, no-ssl3/no-zlib/no-comp/no-autoload-config/no-makedepend; embedded compiler flags and system directories in supplier-build-version.txt. The supplier signing key is not reproduced; source build instructions/provenance are retained, not a claim of bit-identical signed rebuild. Build scripts are evidence only and were not executed.

## Python promotion path and exact delta

Full normal-GIL portable PSF archive, Lib + DLLs and a separate build venv; PyInstaller emits onedir with `_internal`. This is not an embeddable `_pth` migration. Official archive https://www.python.org/ftp/python/3.14.8/python-3.14.8-amd64.zip SHA-256 `4873947a8afc037846b180312b83c744a4146a851cfd316a75c3125a4d8299da` is checked against retained official release manifest. Selected six PSF Authenticode records remain Valid; complete emitted CPython runtime/extension file pins now cover26 files including build python.exe, excluding Microsoft CRT files separately tracked in B2. Whole archive hash covers the coherent runtime. Current23 wheels remain compatible with normalcp314/abi3 and x64; 98 installed package PYDs have no missing imported python314.dll symbol. No package version/hash lock changed.

Exact before/after native and standard-library hashes are in `windows-tls-promotion.json` and its retained raw runtime delta. CPython sources: https://www.python.org/ftp/python/3.14.8/Python-3.14.8.tar.xz SHA-256 `c2215904f02b175596dc49351585104f4bc20341e1c47378b26a2c274360ce73`. Exact PSF OpenSSL source-deps3.5.9 archive: https://github.com/python/cpython-source-deps/archive/refs/tags/openssl-3.5.9.tar.gz SHA-256 `d6cf0d9a651f25fe506f6b3dc133a80b9b79a0bc565f570dcf8fdbd597551485`; recorded against PSF SPDX. Coherent patch also changes embedded Expat 2.8.1 ->2.8.5; source/COPYING retained against PSF SPDX SHA-256. SQLite 3.50.4, bzip2/libffi/mpdecimal/XZ/zlib-ng/zstd identities remain. Tcl/Tk are excluded from shipping; their PSF source-manifest deltas do not add them to distribution.

## Deterministic release inputs and exact OpenSSL hashes

`packaging/windows-tls-inputs.json` is QUALIFIED for TLS inputs. Explicit pinned roots relative to repository: `../WindowsReleaseSuppliers/psf-python-3.14.8` and `../WindowsReleaseSuppliers/firedaemon-openssl-3.5.9/x64/bin`. Default build venv: `../WindowsReleaseSuppliers/build-venv`. Identical files outside these roots are rejected; build interpreter, optional Qt override, source hashes, Analysis origins and bundled membership are checked. Restricted in-process PATH excludes tooling; old3.5.7/3.6.4 hashes, unsupported versions, unknown/duplicate/missing/relocated TLS files remain rejected. Production B1-B5 preflight still refuses RC creation.

| Consumer | Filename | SHA-256 |
| --- | --- | --- |
| python | `libcrypto-3.dll` | `75495fe0e079ab00d49be740d3c710a0b94e3f74f9648cb7cc9f768fc7f52319` |
| python | `libssl-3.dll` | `8957182a9c385bfd9f3f790921de2ddc614cf91f99edbed4e9e5446a46504e32` |
| qt | `libcrypto-3-x64.dll` | `5268a29c9a5e353770b894f3dbd148ee8c60971aa1620713c54d8e56563d0aca` |
| qt | `libssl-3-x64.dll` | `00520a8ca63ec624969742aa04e7db2af94ba0d3f5fe204cbd114b4ec1f24752` |

## Frozen and security qualification

Candidate frozen diagnostic PASS before promotion. Promoted frozen diagnostic PASS, exit0, using production prepare/Analysis/bundle checks: actual main.py startup, normal text input, PDF export and invoice QPixmap preview plugin; Python ssl/verified HTTPS; Qt OpenSSL init/verified HTTPS; both stacks reject an untrusted certificate; local synthetic staging feed, retry after503, SHA verification and checksum mismatch preserving verified bytes. Inert downloaded bytes never executed. Default staging remains offline. SQLite query, NumPy dot, Shapely geometry and pyproj transformation PASS. This is local staging qualification, not public updater/installer E2E.

Loaded root: `<WORKSPACE>/WindowsOpenSslPromotionEvidence/dist/MastixaPromotedTlsDiagnostic/_internal/`. Python libssl-3/libcrypto-3 and Qt -x64 pair all load there; qopensslbackend loads from its bundle-local PySide6/plugins/tls directory. Both runtime version strings3.5.9; Qt build string3.5.4. Exact captured paths/hashes: frozen-runtime.json. No machine/global PATH or old3.5.7/3.6.4 DLL, unknown duplicate or fallback backend. Old diagnostics are preserved outside release inputs and never used for new acceptance.

Fresh authoritative OpenSSL advisory ranges: both final3.5.9 stacks have Critical 0, High 0, known affecting 0; support through 2030-04-08. Classification **ACCEPTABLE FOR RC**, OpenSSL security/version only. Retain historical full23/13-CVE intervals as superseded before-state evidence; do not infer full CPython/Qt/Mesa security certification.

31 focused tests PASS, failures/errors/skips0, Qt messages0, ResourceWarnings0. Exact runtime/hash/source/guard/metadata/schema/determinism/preservation checks are in verification.json. Earlier fixture-only Qt negative-cert attempt reused a verified connection; a fresh QNetworkAccessManager fixed the diagnostic test, and both independent certificate rejection checks passed. No application edit was needed. No full 99-scenario audit or dependency/wheel requalification was restarted.

The full PSF patch also replaces root VCRUNTIME140/VCRUNTIME140_1 14.42.34438.0 with 14.51.36247.0. Frozen loading passed; exact hashes/original names now appear in the manifest/SBOM and the two affected B2 ledger rows. Microsoft grants/recipient rights and 14.51 release status remain UNKNOWN / BLOCKER. CRT names also occur legitimately under wheel directories, so these separate Microsoft inputs are checked by the full supplier archive/metadata rather than mistaken for duplicate OpenSSL DLLs.

## Rights and retention / remaining gates

OpenSSL 3.5.9 Apache2.0 exact upstream LICENSE matches supplier license after line-ending normalization; no upstream NOTICE file exists in the pinned source root. Keep copyright/license/disclaimer text and source/build receipts. Permissive binaries do not create a blanket source-delivery obligation; project policy retains exact archive/source/build/legal/hash receipts while binaries remain available and at least five years after last distribution, indefinitely in the release archive. Full PSF historical chain remains byte-identical; version-specific copy included. Expat 2.8.5 COPYING included. No supplier EXE/sample license is silently applied to the two DLLs.

B1 producer Qt/PDFium/Mesa NOTICE/build/embedded receipts; B2 Microsoft eligible redistribution/recipient evidence; B3 CRS terms/mapping; B4 corresponding nested source and replacement materials remain blocked. B5 OpenSSL work is complete, but prior Mesa maintenance/security/build qualification remains **BLOCKED**. Both readiness flags stay false; no final RC.

**Exact next step:** close the retained Mesa/native B5 qualification in a separately authorized bounded batch, then complete the listed B1-B4 materials. Reuse this pinned OpenSSL evidence unless supplier bytes, source/configuration or consumer inputs change. Do not rerun the TLS audit or 99-scenario matrix merely to resume.

---

# Windows TLS/native qualification — 2026-10-07

**BLOCKED BEFORE RC BUILD. B5 BLOCKED.** RELEASE-INFRA / DESKTOP, Windows x64.
This bounded batch traces both stacks, qualifies a supplier Python patch in an
isolated diagnostic environment and adds production packaging rejection checks.
It does not promote a new shipping runtime or close B1–B4. No final RC, installer,
commit, push, tag, upload or publication occurred.

| Consumer | Retained shipping input | Isolated diagnostic result | Shipping disposition |
| --- | --- | --- | --- |
| Python `_ssl` / `_hashlib` / urllib updater HTTPS | CPython 3.14.6, OpenSSL 3.5.7 | Official complete CPython 3.14.8 x64 archive, OpenSSL 3.5.9; frozen/native/HTTPS checks PASS | 3.5.7 remains **UPDATE REQUIRED**; candidate promotion pending coherent Qt qualification and affected runtime metadata delta |
| Qt 6.11.2 `qopensslbackend` / QNetworkAccessManager, optional explicit OSM HTTPS | OpenSSL 3.6.4 from ambient Poppler PATH | Same exact old pair explicitly copied into an external diagnostic supplier directory; loaded bundle-local; baseline HTTPS PASS | 3.6.4 remains **UPDATE REQUIRED**; no patched Qt supplier binary adopted |

## Before-state mapping

The eight TLS/runtime records and PE imports are retained in the sibling local
`WindowsTlsNativeEvidence/before-mapping.json`. All hashes match the previous
shipping manifest and retained frozen files. The owner's interpreter directory
was inaccessible to this sandbox; its corresponding frozen bytes were inspected
instead, without overwriting or launching the owner runtime.

- Python files: `_internal/libssl-3.dll`, `libcrypto-3.dll`, `_ssl.pyd`,
  `_hashlib.pyd`. `_ssl` imports both OpenSSL DLLs and python314.dll;
  `_hashlib` imports libcrypto-3.dll and python314.dll. OpenSSL imports the
  documented Windows/CRT dependencies; libssl imports its matching libcrypto.
  Source route: `app/update_manager.py` explicit HTTPS feed/download uses urllib;
  default staging remains offline. No updater/network behavior was changed.
- Qt files: `_internal/libssl-3-x64.dll`, `libcrypto-3-x64.dll`,
  `PySide6/plugins/tls/qopensslbackend.dll` and `PySide6/Qt6Network.dll`.
  The Qt DLL/plugin match the qualified PySide6 Essentials 6.11.2 wheel. The
  OpenSSL pair is not in that wheel. It came from the Codex bundled Poppler
  tool's Library/bin PATH entry. The exact hook is PyInstaller 6.22.3
  `QtNetwork.collect_extra_binaries` → `_collect_qtnetwork_openssl_windows` →
  `bindepend.resolve_library_path`, with PATH fallback. Production spec originally
  had empty binaries and no explicit TLS input. Installer collection is the dist
  tree; it propagates whatever Analysis collects, without an independent supplier.
- Actual frozen loading is proven in the retained baseline and refreshed local
  diagnostic loaded-file records, not inferred from plugin presence. Pyproj's
  curl uses Schannel; it is not a third OpenSSL instance.

**PATH contamination existed: reproducibility defect.** The Qt 6.11.2 source
loader, extracted from the retained exact qtbase archive, requests only the
`libssl-3-x64` / `libcrypto-3-x64` names on Windows x64. In-process clean-PATH
probing falls back to Schannel, rather than loading CPython's unrenamed DLLs.
No ad-hoc rename, independent Python DLL swap or silent backend change was used.

## Supplier route and exact candidate files

The [official Python 3.14.8 release](https://www.python.org/downloads/release/python-3148/)
includes OpenSSL 3.5.9. The complete normal-GIL x64 runtime was downloaded using
the [official release manifest](https://www.python.org/ftp/python/3.14.8/windows-3.14.8.json),
then extracted under the external evidence directory. It changes neither the
owner interpreter nor existing environments. The 23 existing qualified wheel
archives were installed offline with the unchanged exact hash lock; no wheel
qualification or unrelated package upgrade was repeated.

Supplier archive: `https://www.python.org/ftp/python/3.14.8/python-3.14.8-amd64.zip`
SHA-256: `4873947a8afc037846b180312b83c744a4146a851cfd316a75c3125a4d8299da`.
Six runtime/extension files have Valid Authenticode signatures from the Python
Software Foundation, recorded with exact hashes/signers in local
`python-signatures.json`; the coherent pins are in `packaging/windows-tls-inputs.json`.

| DLL | Retained shipping SHA-256 | Isolated diagnostic SHA-256 |
| --- | --- | --- |
| libssl-3.dll | b17a87979862d19241edc4318f967e24c3ec356ed6c2368f561179fab2311001 | 8957182a9c385bfd9f3f790921de2ddc614cf91f99edbed4e9e5446a46504e32 |
| libcrypto-3.dll | 53c529145339fb042a3dcd3a09c2d7753204f8b4fc79d99e0d31e69a33985958 | 75495fe0e079ab00d49be740d3c710a0b94e3f74f9648cb7cc9f768fc7f52319 |
| libssl-3-x64.dll | a534aa89400514686acabf62e6b1144bf5890f55f2ed740d10e4f43a0b7b7f04 | unchanged old Qt baseline only |
| libcrypto-3-x64.dll | bd33fac597f4f910fba036d5618b1ee4df74a83807cc80b384e24228afdc14af | unchanged old Qt baseline only |

No usable patched artifact was identified in the checked authoritative supplier
routes: [Qt's OpenSSL x64 feed](https://download.qt.io/online/qtsdkrepository/windows_x86/desktop/tools_opensslv3_x64/qt.tools.opensslv3.win_x64/)
still provides 3.0.16. The [upstream Windows installer announcement](https://www.openssl-corporation.org/blog/windows-installer.html)
describes a testing 4.0.1 package. Neither is a suitable patched replacement for
this qualification. This is a finding about the inspected public channels,
not proof that no qualified commercial supplier or controlled build exists.
No broad Python/Qt upgrade is established as necessary. A supported coherent
OpenSSL 3 binary supplier/build route is the missing input.

## Narrow production packaging protection

`packaging/tls_inputs.py`, the spec and build script now fail closed until the
explicit supplier lock is qualified. The lock deliberately remains BLOCKED.
Future inputs require exact filenames, hashes, version/security classification,
immutable archive receipt and explicit supplier roots. Analysis runs with a
restricted in-process PATH; external Qt/plugin/OpenSSL configuration is cleared
for discovery. Source paths and coherent Python TLS/runtime pins are checked
after Analysis. Bundle membership/hashes are checked before installer collection.
Unknown, old, duplicate, relocated, missing and arbitrary tooling/PATH copies
are rejected, including identical DLL bytes outside the approved source root.
These are build checks; no installed-library hash restriction was introduced.

This removes ambient TLS discovery as an acceptable release path. It does not
make the absent Qt supplier pair reproducible or claim successful RC packaging.
Production readiness still refuses exactly the existing five blockers.

## Security qualification and tests

Only final candidate OpenSSL 3.5.9 was requalified against freshly retained
official advisory ranges. Its OpenSSL security/version classification is
**ACCEPTABLE FOR RC**, with zero currently listed affecting Critical/High issues
(and zero affecting records for 3.5.9). [OpenSSL's policy](https://openssl-library.org/policies/releasestrat/)
supports 3.5 LTS through 2030-04-08. Runtime promotion remains blocked; this is
not a blanket CPython/native security certification. Maintenance is through
coherent official CPython patch packages, never independent DLL replacement.

Actual retained shipping stacks remain **UPDATE REQUIRED**. The existing full
23-CVE Python and 13-CVE Qt interval ledger is unchanged, including the High
DTLS advisory and HTTPS-reachable certificate processing. Absence of inspected
DTLS/QUIC/CMP use is not a library exemption. Qt 3.6 support ends 2026-11-01.

- **29 unique focused tests PASS**, with final changed guard tests rechecked;
  zero failures/errors/skips, Qt messages and ResourceWarnings.
- Frozen diagnostic exit 0: actual main.py startup, normal input, report export
  and PDF preview, Python ssl/version, local certificate/hostname-validating
  updater HTTPS, failed-download retry, SHA verification, mismatch rejection
  preserving verified bytes, rejection of an untrusted certificate, default
  offline staging and Qt OpenSSL baseline HTTPS. Inert synthetic download bytes
  were never executed. Local staging does not constitute public updater E2E.
- All four OpenSSL DLLs and qopensslbackend loaded from the diagnostic bundle;
  exactly two designed filename pairs, no duplicate/unknown TLS DLLs, no old
  Python 3.5.7 bytes. Old Qt 3.6.4 remains explicitly and deliberately present
  only in the unqualified baseline; patched Qt runtime validation is blocked.
- **33 targeted checks PASS**: supplier archive/signatures, coherent frozen pins,
  exact TLS membership, loaded paths, lock regenerated twice with identical
  bytes, retained wheel/SBOM/source/legal/readiness hashes and spec syntax.
  PowerShell parse PASS; git diff --check PASS recorded in final verification.

The initial diagnostic driver incorrectly hid bundle-local Qt lookup while
restricting PATH; only that external harness was repaired. Production application
source was unchanged. No full 99-scenario audit, dependency inventory, unrelated
legal regeneration or final RC was performed.

## Promotion boundary and exact next step

No shipping component changed, so existing notices, source plan, license inventory,
shipping hash manifest and SBOM remain byte-identical and accurately describe
the retained 3.14.6/3.5.7 + Qt 3.6.4 surface. The diagnostic is not substituted into
them. The new spec guard invalidates use of the old Analysis as proof of future
release output; a coherent supplier-qualified future diagnostic must establish it.

**B5 BLOCKED:** obtain an authoritative coherent Windows x64 Qt-compatible
OpenSSL 3.6.5 pair, or explicitly qualify another supported patched OpenSSL 3
build with original archive/source/configuration/build receipts. Fill the supplier
lock only after qualification; combine with the PSF 3.14.8 patch candidate,
rerun affected frozen/TLS checks, then update only actual runtime/OpenSSL/native
source/notice/hash/SBOM deltas. Do not reuse the old Qt diagnostic as security
acceptance. Mesa maintenance/security/build closure also remains a B5 gap.
B1 producer notices/build receipts, B2 Microsoft grants, B3 CRS terms and B4
matching source/replacement materials retain their previous blocked readiness.
