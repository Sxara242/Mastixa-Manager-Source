> Retained historical engineering record, sanitized for public review.
> Current status: [RELEASE_STATUS.md](RELEASE_STATUS.md). This record does not
> establish approval of the current source or a new binary release. Local-only
> receipt paths refer to privately retained evidence, absent from this snapshot.

# B2 CRT normalization — 2026-10-08

**B2 PASS.** RELEASE-INFRA / DESKTOP, Windows x64. B1/B3/B4 remain BLOCKED;
B5 PASS RETAINED, unchanged. **BLOCKED BEFORE RC BUILD.** This leading section
supersedes older B2 grant/CRT-shipping findings below; those are historical.

Chosen route: zero Microsoft CRT DLL/installer shipment; recipient independently
installs official x64 VC Redist >=14.51.36247.0. Mastixa Setup checks registry
Installed/version plus5 canonical System32 files and rejects missing/older
prerequisites. No auto-download, global installation or Microsoft file rename.
All13 former CRT cases are NOT SHIPPED;5 unsigned third-party importers are
deterministically normalized to msvcp140.dll with exact input/output SHA256 locks.
Production policy matches the successfully validated central frozen bytes.
Planned native114->101; pure1216/data456 retained; SBOM137 shipping components
plus1 explicitly external runtime prerequisite. The44 OS exclusions are unchanged.

Exact per-file/importer/provenance/model/test/rights decision:
`WINDOWS_CRT_NORMALIZATION.md`, `windows-crt-normalization.json`,
`packaging/crt_policy.py`, `packaging/windows-crt-policy.json`, and sibling
`../WindowsB2NormalizationEvidence/`. Source suppliers/wheel lock are untouched.
Frozen baseline/app-local/central checks,1243-symbol correspondence, actual
CRT-path tracing and controlled-search/clean-no-Redist simulation PASS.
No pristine VM or final RC was created. Native Inno prerequisite probe aborts
before installation. Later actual RC install/upgrade acceptance remains required.

Community2026 entitlement is documented separately from recipient runtime
installation. No Microsoft code/installer is redistributed by this route;
recipient installation carries Microsoft's terms. Conditional official app-local
deployment passed diagnostics but is NOT adopted. Its protective downstream
assent conditions would remain necessary if later chosen.

Original retained source-candidate ZIPs still describe their prior captured
bytes. They were not relabeled/refreshed and do not match this new checkpoint.
B4 source/replacement gaps and both readiness flags remain unchanged/false.
No full audit, B1/B3/B4/B5 rerun, UI/performance/Android change, RC build,
commit/push/tag/publication, global install or antivirus change. Next release
action: close the retained B1/B3/B4 gaps, then final preflight; RC requires a
later authorized artifact batch and the retained Bitdefender rule.

---

# B2 Community installation re-evaluation — 2026-10-07

**B2 BLOCKED.** RELEASE-INFRA / DESKTOP; B2 only. This section supersedes the
historical VS Code-only/no-Visual-Studio finding and older blanket lack-of-own-license
claims below. B1/B3/B4 remain BLOCKED at their retained external-rights checkpoint;
B5 PASS RETAINED, unchanged. No RC build, installer execution, dependency audit,
B5/OpenSSL/Mesa qualification, commit, push, tag or publication.

Visual Studio Community 2026 **18.10.3**, installation build **18.10.12224.181**,
stable/non-prerelease, installed at `C:/Program Files/Microsoft Visual Studio/18/Community`.
Only MSVC toolset directory: **14.51.36231**; actual x64 compiler **19.51.36260.0**.
Installed Desktop development with C++, latest x64/x86 tools, VC Redist and
Windows 11 SDK **10.0.26100.0** are confirmed from local setup metadata.
Owner attests legal installation and accepted Community terms; sign-in is not
the entitlement evidence.

Redist root: `C:/Program Files/Microsoft Visual Studio/18/Community/VC/Redist/MSVC/14.51.36231`.
`v145/` is the installed installer alias directory. Exact x64 release CRT files
are in `14.51.36231/x64/Microsoft.VC145.CRT/`; versions are **14.51.36247.0**.
Official `vc_redist.x64.exe` and `vc_redist.x86.exe` at that root are both
14.51.36247.0, valid Microsoft signatures. x64 SHA256:
`843068991daaa1f73ad9f6239bce4d0f6a07a51f18c37ea2a867e9beca71295c`;
x86 SHA256: `f0bab33a302b3cdb2e11113760d016f54fd3d2632c65ba7834fac4f0abd7f1a3`.
The x64 installer matches the retained official Microsoft download exactly.

The [Community2026 license](https://visualstudio.microsoft.com/license-terms/vs2026-ga-community/)
dated October1,2025 grants conditional object-code redistribution from its
[2026 Distributable List](https://learn.microsoft.com/en-us/visualstudio/releases/2026/redistribution).
The local Community package `_package.json` license link2327616 resolves to that
edition's license page; installed `Licenses/1033/Redist.txt` points to the same
2026 list. Original DOCX SHA256:
`02ac07637f4a513a807cd3721c7620433fc483bc049d25784b0c10c54b05e1fb`.
The list covers files under `VC/redist` subject to the license, prohibits
modification and excludes debug_nonredist. The standalone runtime install/use
license is not the distribution grant; the accepted Community license supplies it.

**Conditional right established for Mastixa's use of listed unmodified official
release code.** It does not establish a blanket right for every older supplier
copy or changed filename. Mastixa supplies primary application functionality.
Before distribution, external recipients/distributors must agree to protective
Microsoft terms; Microsoft indemnification and other distribution restrictions
also apply. Current Inno `LicenseFile=..\LICENSE` accepts only the application
AGPL license. Protective Microsoft assent remains unproved. Keep CRT terms
separate from AGPL/LGPL rights; preserve covered-library replacement rights.

Raw local metadata, original Microsoft downloads, all official Redist file paths,
versions/hashes, signature receipts and the13 current source-file comparisons:
`../WindowsB2CommunityEvidence/`. Exact current per-file decision:
`windows-microsoft-runtime.json` (`community_2026_evaluation` and each shipping
file's `community_2026` object). No shipping byte or filename was changed.

## Exact13-file mapping

Source aliases expand to these absolute paths:

- `W/` = `<WORKSPACE>/WindowsReleaseSuppliers/build-venv/Lib/site-packages/`
- `P/` = `<WORKSPACE>/WindowsReleaseSuppliers/psf-python-3.14.8/`
- `O/` = `C:/Program Files/Microsoft Visual Studio/18/Community/VC/Redist/MSVC/14.51.36231/x64/Microsoft.VC145.CRT/`

Every `O/` counterpart is14.51.36247.0 and covered by the2026 directory-based
Distributable List. Exact older current copies are not proven by that directory
grant merely because their canonical basenames match. The following status
applies to current bytes/names, not a hypothetical future replacement.

| Shipping path under `_internal/` | Exact current source | Current version | Official counterpart | Byte/hash match | Current classification |
| --- | --- | --- | --- | --- | --- |
| `PySide6/MSVCP140.dll` | `W/PySide6/MSVCP140.dll` | 14.44.35211.0 | `O/msvcp140.dll` | NO; different version | **UNKNOWN — BLOCKER** |
| `PySide6/MSVCP140_1.dll` | `W/PySide6/MSVCP140_1.dll` | 14.44.35211.0 | `O/msvcp140_1.dll` | NO; different version | **UNKNOWN — BLOCKER** |
| `PySide6/MSVCP140_2.dll` | `W/PySide6/MSVCP140_2.dll` | 14.44.35211.0 | `O/msvcp140_2.dll` | NO; different version | **UNKNOWN — BLOCKER** |
| `PySide6/VCRUNTIME140.dll` | `W/PySide6/VCRUNTIME140.dll` | 14.44.35211.0 | `O/vcruntime140.dll` | NO; different version | **UNKNOWN — BLOCKER** |
| `PySide6/VCRUNTIME140_1.dll` | `W/PySide6/VCRUNTIME140_1.dll` | 14.44.35211.0 | `O/vcruntime140_1.dll` | NO; different version | **UNKNOWN — BLOCKER** |
| `Shapely.libs/msvcp140-90bc62d4947a5878f1dc1057312f3be2.dll` | `W/Shapely.libs/msvcp140-90bc62d4947a5878f1dc1057312f3be2.dll` | 14.44.35215.0 | `O/msvcp140.dll` | NO; different version | **UNKNOWN — BLOCKER** |
| `VCRUNTIME140.dll` | `P/VCRUNTIME140.dll` | 14.51.36247.0 | `O/vcruntime140.dll` | YES | **REDISTRIBUTABLE — APP LOCAL** |
| `VCRUNTIME140_1.dll` | `P/VCRUNTIME140_1.dll` | 14.51.36247.0 | `O/vcruntime140_1.dll` | YES | **REDISTRIBUTABLE — APP LOCAL** |
| `numpy.libs/msvcp140-a4c2229bdc2a2a630acdc095b4d86008.dll` | `W/numpy.libs/msvcp140-a4c2229bdc2a2a630acdc095b4d86008.dll` | 14.40.33810.0 | `O/msvcp140.dll` | NO; different version | **UNKNOWN — BLOCKER** |
| `pyproj.libs/msvcp140-7c26614e1d733892c2deac7e245ce115.dll` | `W/pyproj.libs/msvcp140-7c26614e1d733892c2deac7e245ce115.dll` | 14.51.36247.0 | `O/msvcp140.dll` | YES | **UNKNOWN — BLOCKER** |
| `shiboken6/MSVCP140.dll` | `W/shiboken6/MSVCP140.dll` | 14.44.35211.0 | `O/msvcp140.dll` | NO; different version | **UNKNOWN — BLOCKER** |
| `shiboken6/VCRUNTIME140.dll` | `W/shiboken6/VCRUNTIME140.dll` | 14.44.35211.0 | `O/vcruntime140.dll` | NO; different version | **UNKNOWN — BLOCKER** |
| `shiboken6/VCRUNTIME140_1.dll` | `W/shiboken6/VCRUNTIME140_1.dll` | 14.44.35211.0 | `O/vcruntime140_1.dll` | NO; different version | **UNKNOWN — BLOCKER** |

Two root VCRUNTIME copies are **REDISTRIBUTABLE — APP LOCAL**, subject to the
Community distribution conditions. The other eleven are **UNKNOWN — BLOCKER**.
Eight older Qt/shiboken files have valid Qt Company signatures, not a demonstrated
match to their canonical Microsoft originals. Both older renamed MSVCP copies
have valid Microsoft signatures, but do not match the installed newer Redist;
no binary modification is inferred solely from that version/hash difference.
The pyproj renamed copy matches official Microsoft msvcp140.dll bytes and PE
sections exactly. Full SHA256, original filename, source path, counterpart hash,
signature, list membership, app-local condition, installer preference and rename
flags are recorded individually in JSON.

All13 are release MSVC CRT, not OS-only UCRT. All **44 OS-PROVIDED — EXCLUDE**
rows remain unchanged and nonshipping. No debug_nonredist file was added.
No current file is classified NOT REDISTRIBUTABLE solely because its right is
unresolved. No existing copy is classified REDISTRIBUTABLE — OFFICIAL VC REDIST
ROUTE as though installation could resolve its current bytes/name automatically.

Official x64 release directory contains exactly: `concrt140.dll`, `msvcp140.dll`,
`msvcp140_1.dll`, `msvcp140_2.dll`, `msvcp140_atomic_wait.dll`,
`msvcp140_codecvt_ids.dll`, `vccorlib140.dll`, `vcruntime140.dll`,
`vcruntime140_1.dll`, `vcruntime140_threads.dll`. All10 are version14.51.36247.0
and validly Microsoft-signed. The complete installed Redist-only ledger also
records x86, OneCore, MFC/OpenMP and prohibited debug files; these extra files
are not Mastixa shipping additions.

## Renamed MSVCP result and packaging route

Original canonical Microsoft DLL for all three: `msvcp140.dll`.

- Shapely2.1.2 expects `msvcp140-90bc62d4947a5878f1dc1057312f3be2.dll`
  (14.44.35215.0); both bundled GEOS and GEOS C DLLs import this name.
- NumPy2.5.3 expects `msvcp140-a4c2229bdc2a2a630acdc095b4d86008.dll`
  (14.40.33810.0); `_multiarray_umath` and `_pocketfft_umath` import this name.
- pyproj3.8.0 expects `msvcp140-7c26614e1d733892c2deac7e245ce115.dll`
  (14.51.36247.0); bundled `proj_9` imports this name. Its Microsoft original
  is byte-identical, SHA256
  `7c26614e1d733892c2deac7e245ce115504b1d80592dd0a01b08e3e5a55f89ca`.

**Renamed redistribution is not clearly authorized.** The official list requires
unmodified files; the grant does not expressly allow renaming. A pure filename
rename is not proved to be a prohibited binary modification, and this review
does not declare that it necessarily violates the agreement. It also does not
assume that identical bytes authorize a different filename. Keep all three
blocked until explicit Microsoft permission or a canonical technical route.

The official installer supplies canonical names and **cannot satisfy any of
these hashed imports as currently packaged**. No installed Redist setting
changes those import names. The cleanest alternative is supplier-built or
reproducibly rebuilt/repackaged third-party GEOS/Shapely, NumPy and PROJ/pyproj
with canonical `msvcp140.dll` imports. Change third-party build/repair configuration,
not Microsoft DLLs. [delvewheel's own documentation](https://github.com/adang1345/delvewheel#usage)
provides `repair --exclude msvcp140.dll` for a central-runtime dependency or
`--no-mangle msvcp140.dll` when retaining a licensed canonical app-local copy.
Use those options on fresh unmangled builds; they do not undo current repaired
wheels. No rebuild/repackage/import patch is performed in this evaluation.

[Microsoft recommends the official installer for servicing](https://learn.microsoft.com/en-us/cpp/windows/redistributing-visual-cpp-files).
Preferred proposed route: unchanged official x64 VC Redist14.51.36247.0 (or a
later explicitly qualified version), all CRT imports canonical, then no Mastixa
CRT copies. Check architecture and Installed/version, skip equal/newer runtimes,
otherwise execute an explicit prerequisite with `/install /passive /norestart`,
handle0/3010 and recheck; preserve meaningful error handling and reboot behavior.
The new Community grant permits distributing that listed unchanged installer,
subject to its protective downstream conditions. Prior independent-user-download
fallback remains available; it is no longer needed just to avoid lack of own VS
license. No automatic download, system installer or packaging change was made.

Remaining exact B2 gaps: older10 originals/code correspondence and applicable
prior-release grants; all3 filename permissions or canonical rebuild; protective
recipient/distributor assent; tested canonical CRT packaging route. A subsequent
bounded CRT-only qualification must verify canonical imports, frozen startup,
PDF/input/NumPy/GIS/native loading and installer runtime detection on clean
Windows. It must preserve the existing B5 inputs; no full inventory or prior
audit rerun is requested by this checkpoint.


---

# External rights / supplier evidence checkpoint — 2026-10-07

**BLOCKED BEFORE RC BUILD.** Authoritative current supplement, RELEASE-INFRA / DESKTOP. B5 PASS retained without changes or reruns. Full decisions/evidence: `WINDOWS_EXTERNAL_RIGHTS_CLOSURE.md`, `windows-external-rights-closure.json`, sibling `WindowsExternalRightsEvidence`. Previous sections below retain their historical checkpoints.

| Gate | Status | Evidence | Remaining action |
| --- | --- | --- | --- |
| B1 | BLOCKED | QtImageformats552 source hashes; exact OpenBLAS producer/source/recipe; binding identity | QtPdf GN/compiled graph; executed binding and GCC/toolchain producer receipts |
| B2 | BLOCKED | Microsoft primary license/docs, PSF Windows binary conditions, host probes |13-file applicable grants/downstream terms or qualified no-CRT/user-installed prerequisite route |
| B3 | BLOCKED | Unchanged proj.db and retained correspondence; targeted EPSG customization/input review | Esri/NKG exact derivation; IGNF/ITRF/IAU/init rights; EPSG modification compliance |
| B4 | BLOCKED | Added matching sources/build scripts/patch; no post-install DLL hash guard; SDK26 smoke retained | Full executed build/generator materials and usable recipient-built modified-library replacement |
| B5 | PASS RETAINED | TLS3.5.9 and Mesa exclusion evidence reused unchanged | none |

Closed: QtImageformats exact source commit/archive and552 supplier hash correspondence; actual8-file binding identity; OpenBLAS exact producer wheel/DLL, pinned source, patch/Windows recipe; static GCC presence; Microsoft own-license vs supplier-distributor distinction and original PSF Windows binary conditions; EPSG upstream modification classification; build-time vs installed-library guard review and explicit update/repair overwrite behavior.

Still blocked: exact QtPdf compiled GN/producer graph; executed binding/GCC toolchain and GEOS build/generator/replacement materials;13 CRT applicable grants/downstream terms or qualified no-CRT route; Esri/NKG exact derivation, IGNF/ITRF/IAU/init rights and complete EPSG modification compliance. Both readiness flags remain false. Final pre-RC preflight NOT RUN, because B1-B4 are not all PASS. RC may not be built.

Owner reports VS Code only; host probes discover no VS/Build Tools. Microsoft installer redistribution/chaining still needs rights; independent recipient download/install avoids Mastixa copying it, but3 hashed MSVCP imports prevent blind removal of13 app-local CRTs. No system installer executed or entitlement assumed.

New required legal/source records justify only a deterministic source-candidate refresh. Original741-file archive and all retained Qt26/database/TLS/Mesa/wheel/usage evidence remain unchanged. Focused validation and exact Git/preservation receipt are in `../WindowsExternalRightsEvidence/final-report.json` and `preservation-final.json`; no full audit or native qualification is repeated.

Exact next owner action: establish the chosen Microsoft distribution route and obtain the listed missing supplier/CRS/replacement receipts. Then close only those gaps; final preflight is permitted only after B1-B4 PASS. No commit/push/tag/publication/final RC build.

The direct-license and supplier-distributor distinction plus exact per-file runtime ledger are current in windows-microsoft-runtime.json. Official PSF Windows binary Additional Conditions are now included. Independent user installation is the preferred no-copy fallback, not a permission to chain or remove hashed dependencies.

---

# Final Microsoft decision — 2026-10-07

**B2 BLOCKED.** Retain the13 app-local CRT records and44 OS exclusions; do not
replace them with an unqualified system-install assumption. The official signed
VC14 x64 installer14.51.36247.0 was downloaded and statically inspected, never
executed. Its two VCRUNTIME and pyproj MSVCP files match shipping SHA256 exactly;
the pyproj hashed filename is only a rename for this byte-identical file, not
evidence of a binary repair. Other ten CRTs are not proven by this container.

[Microsoft redistribution documentation](https://learn.microsoft.com/en-us/cpp/windows/redistributing-visual-cpp-files)
limits distribution to eligible licensed VS users and applicable license terms.
The standalone installer [original terms](https://visualstudio.microsoft.com/wp-content/uploads/2025/10/Visual-C-V14-License-Redistributable_and_Runtime_ENU.docx)
allow install/use but restrict distribution; downloading it is not a separate
redistribution grant. Supplier wheel permissive licenses do not replace those
conditions. Release-name/runtime behavior is not proof of entitlement.

Proposed qualified installer route is x64 v14 >=14.51.36247.0, registry version+
Installed=1 detection in the appropriate view, skip newer/equal, otherwise
official installer `/install /passive /norestart`, handle0/3010 and recheck.
This route is documented, not implemented/executed, while the grant is blocked.
Removing app-local files would also require resolving mangled import names and
validating the supported runtime/ABI route separately. No owner system changes.
Exact installer/hash/signature/license and per-file ledger in
`windows-microsoft-runtime.json`; original evidence in WindowsFinalB1B4Evidence.

---

# PSF runtime promotion delta - 2026-10-07

**B2 remains UNKNOWN / BLOCKER.** The coherent official PSF Python 3.14.8 patch changes only the two root VCRUNTIME140.dll / VCRUNTIME140_1.dll inputs from 14.42.34438.0 to 14.51.36247.0. Exact new supplier/hash/version/original-name entries and before-state receipts are in windows-microsoft-runtime.json and the native delta manifest. Valid runtime behavior and an official PSF archive are not an independent Microsoft redistribution grant. Existing recipient/eligible release/redist rights and 14.51 release-status requirements remain unresolved. Other CRT rows and 44 OS exclusions remain unchanged.

---

# Microsoft runtime disposition — 2026-10-07

**B2 BLOCKED.** `windows-microsoft-runtime.json` lists every Microsoft-origin
file found in the retained PE inventory: exact path/name, PE original filename,
file version, product, SHA-256, origin, shipping flag, disposition and remaining
grant. It reconciles to **13 shipping release CRT files and 44 already-excluded
OS files**. No debug CRT, Windows SDK utility or other Microsoft-origin binary
was found on this exact candidate surface. This is not a new whole-machine scan.

| Shipping paths under `_internal/` | File version | Origin / classification |
| --- | --- | --- |
| `PySide6/MSVCP140.dll`, `MSVCP140_1.dll`, `MSVCP140_2.dll`, `VCRUNTIME140.dll`, `VCRUNTIME140_1.dll` | 14.44.35211.0 | Essentials 6.11.2 qualified wheel; **UNKNOWN / BLOCKER** applicable grant |
| `shiboken6/MSVCP140.dll`, `VCRUNTIME140.dll`, `VCRUNTIME140_1.dll` | 14.44.35211.0 | shiboken6 6.11.2 qualified wheel; **UNKNOWN / BLOCKER** applicable grant |
| root `VCRUNTIME140.dll`, `VCRUNTIME140_1.dll` | 14.42.34438.0 | CPython installation; **UNKNOWN / BLOCKER** original package/grant |
| `Shapely.libs/msvcp140-90bc62d4947a5878f1dc1057312f3be2.dll` | 14.44.35215.0 | Shapely 2.1.2 qualified wheel; **UNKNOWN / BLOCKER** original grant / modification correspondence |
| `numpy.libs/msvcp140-a4c2229bdc2a2a630acdc095b4d86008.dll` | 14.40.33810.0 | NumPy 2.5.3 qualified wheel; same unresolved grant |
| `pyproj.libs/msvcp140-7c26614e1d733892c2deac7e245ce115.dll` | 14.51.36247.0 | pyproj 3.8.0 qualified wheel; exact VS release/preview status and grant unproven |

All 44 UCRT/API-set copies classify **OS-PROVIDED — EXCLUDE**, retaining the
existing tested Windows 10+ exclusion. Their individual versions/hashes are in
the JSON, rather than guessed from a generic Windows version. MSVC release CRT
is distinct from OS UCRT. Repeated Qt/shiboken filenames are directory-local
copies; matching duplicates are documented, not independently assumed grants.

[Microsoft redistribution guidance](https://learn.microsoft.com/en-us/cpp/windows/redistributing-visual-cpp-files)
and the [2022](https://learn.microsoft.com/en-us/visualstudio/releases/2022/redistribution)/
[2026 REDIST lists](https://learn.microsoft.com/en-us/visualstudio/releases/2026/redistribution)
make distribution conditional on applicable Visual Studio licensing and eligible
unmodified release code. Debug/nonredist and preview code are excluded. Wheel
presence, valid signatures and LGPL application licensing cannot supply that
grant. Obtain supplier/original REDIST provenance and the applicable recipient
distribution rights; compare mangled DLLs to originals to establish whether any
binary modification occurred. No actual modification is inferred from a hashed
filename alone. No owner Visual Studio entitlement has been established here.

The [official VC v14 installer guidance](https://learn.microsoft.com/en-us/cpp/windows/latest-supported-vc-redist)
requires compatible x64 code and a runtime at least as recent as the compiler.
[Microsoft UCRT guidance](https://learn.microsoft.com/en-us/cpp/windows/universal-crt-deployment)
supports Windows-serviced UCRT on Windows 10+. The official-installer alternative
does not waive installer redistribution rights if Mastixa bundles that installer.
A user-installed official prerequisite can avoid Mastixa copying CRT files,
subject to resolving actual dependent names and load behavior.

Preferred direction if grants cannot be established: a checked official VC v14
x64 prerequisite with no Mastixa CRT copies. **Not low-risk for this candidate**:
three wheels import hashed MSVCP names; deleting them and installing the generic
runtime does not supply those names. Rebuild/repackage compatible wheels or use
a supplier-approved remapping strategy, then test native loading, frozen
startup/input/PDF, NumPy, GIS and installer prerequisite behavior on a clean
Windows environment. Do not silently binary-patch Microsoft files or add
automatic installer downloading. Canonical copies also need dependency/loading
validation before removal. No installer/spec/exclusion direction was implemented
without that evidence, and no file is classified NOT REDISTRIBUTABLE merely
because its conditional grant remains unknown.
