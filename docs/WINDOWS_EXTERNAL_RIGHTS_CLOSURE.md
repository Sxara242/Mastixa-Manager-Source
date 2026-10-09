> Retained historical engineering record, sanitized for public review.
> Current status: [RELEASE_STATUS.md](RELEASE_STATUS.md). This record does not
> establish approval of the current source or a new binary release. Local-only
> receipt paths refer to privately retained evidence, absent from this snapshot.

# B2 canonical CRT delta — 2026-10-08

**B2 PASS; B1/B3/B4 BLOCKED; B5 PASS RETAINED.** Only B2 was evaluated here.
The current no-copy prerequisite and hash-locked third-party import normalization
remove all13 former Microsoft shipments; zero current UNKNOWN CRT items.
See WINDOWS_CRT_NORMALIZATION.md and windows-crt-normalization.json. The B1/B3/B4
gate objects/source receipts remain unchanged. Older B2 requirements below
describe the retired app-local/hashed surface; protective downstream assent is
not treated as waived for a future Microsoft-code redistribution route.
Final preflight NOT RUN. BLOCKED BEFORE RC BUILD.

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

| Gate | Retained status | Exact remaining gap |
| --- | --- | --- |
| B1 | BLOCKED | QtPdf executed GN/compiled dependency/patch/toolchain graph; binding generation/header/config/producer receipt; executed OpenBLAS/GCC runtime/toolchain receipt |
| B2 | BLOCKED |2 exact canonical files covered,11 current copies UNKNOWN; older-original correspondence,3 rename permissions/canonical dependency rebuild, protective downstream assent and qualified CRT route |
| B3 | BLOCKED | Exact Esri4 discrepant transformations/usage and NKG member derivation; IGNF3.1.0/ITRF/IAU and inherited init-data rights; EPSG permitted-modification/numerical-equivalence conditions |
| B4 | BLOCKED | Executed QtPdf/binding/GEOS/GCC build/generator/patch/toolchain materials; usable recipient-built modified-library replacement; final source/artifact binding and delivery |
| B5 | PASS RETAINED | No changes or reruns |

Both readiness flags remain false. Final pre-RC preflight NOT RUN. **BLOCKED
BEFORE RC BUILD.** Other gate statuses/materials are preserved; no B1/B3/B4
re-evaluation was undertaken. Retained source-candidate ZIPs describe their
prior captured source/docs and remain unchanged; these new B2 documentation
bytes are not claimed to match those archive hashes.

Exact next step: obtain supplier canonical originals/redistribution receipts and
Microsoft filename-rename authorization, or qualify a bounded third-party
canonical-import rebuild/repackage with licensed official CRT deployment.
Prepare separate protective Microsoft recipient/distributor terms. Keep B2
blocked until all13 current entries are covered or explicitly replaced/removed
under that tested route. Only after B1–B4 PASS may final preflight precede an RC
build. No commit/push/tag/publication is authorized by this checkpoint.


---

# External rights / supplier evidence closure — 2026-10-07

**BLOCKED BEFORE RC BUILD.** RELEASE-INFRA / DESKTOP. This is the authoritative current B1-B4 supplement; previous sections remain historical evidence. No RC or diagnostic rebuild, global installation, external message, upload, commit, push, tag or publication.

| Gate | Status | Evidence | Remaining action |
| --- | --- | --- | --- |
| B1 | BLOCKED | QtImageformats552 source hashes; exact OpenBLAS producer/source/recipe; binding identity | QtPdf GN/compiled graph; executed binding and GCC/toolchain producer receipts |
| B2 | BLOCKED | Microsoft primary license/docs, PSF Windows binary conditions, host probes |13-file applicable grants/downstream terms or qualified no-CRT/user-installed prerequisite route |
| B3 | BLOCKED | Unchanged proj.db and retained correspondence; targeted EPSG customization/input review | Esri/NKG exact derivation; IGNF/ITRF/IAU/init rights; EPSG modification compliance |
| B4 | BLOCKED | Added matching sources/build scripts/patch; no post-install DLL hash guard; SDK26 smoke retained | Full executed build/generator materials and usable recipient-built modified-library replacement |
| B5 | PASS RETAINED | TLS3.5.9 and Mesa exclusion evidence reused unchanged | none |

QtImageformats source pin is PASS: official Qt6.11.2 source archive SHA256 `cecd8900f34b6550076309bc94f62f828008b633a4239e0a08c86788f41001f8`, `.tag`/annotated v6.11.2 commit `47b6139dda3b84d1d3ec15caf8d04eff8d744c8d`. All552 supplier source-SBOM SHA1 checks match:139 exact bytes and413 only after deterministic LF->CRLF conversion. No unexplained changes. Retained5 plugin PE-section correspondence links this source to actual shipping ICNS/TGA/TIFF/WBMP/WebP, with supplier MSVC19.44.35227.0/CMake3.30.5/Ninja1.10.2 receipts and TIFF4.7.2/WebP1.6.0. The LF/CRLF transform is recorded, not called binary equality.

Binding means QtCore/Gui/Widgets/Network/PrintSupport generated C++ Python wrappers, pyside6.abi3.dll, Shiboken.pyd and shiboken6.abi3.dll. Their8 exact hashes/origins and source type-system/generator input manifest are retained. QtPdf/QtPdfWidgets Python wrappers do not ship; qpdf is the Qt C++ image plugin. Exact producer generation/header/config/patch/compiler correspondence remains missing.

OpenBLAS actually ships at `_internal/numpy.libs/libscipy_openblas64_-ed4f167a5330424524f45258e7ca2c8d.dll`, SHA256 `ed4f167a5330424524f45258e7ca2c8d7f03c0cba1f30ee4985553ac1f88ecf8`. The exact producer wheel SHA256 `ea34bf76b8427ac2eca7a99334cbd8937a040303fa8364f9ed8e667d7c8e2c7d` has byte-identical DLL. Runtime export reports0.3.34.106.0/USE64BITINT/DYNAMIC_ARCH/NO_AFFINITY/MAX_THREADS24. MacPython producer commit78fc0eaf6de71d92fd98f74f7e5bfa356a2f83e3 pins OpenBLAS `v0.3.34-106-g446c436e`; exact sources and Windows build/patch/workflow retained. Workflow pins Rtools4.0.0.20220206 and static GCC linking. This is a recipe, not proof of the executed compiler/static runtime build. Static GCC/libgfortran is PRESENT; standalone GCC/libstdc++/libgfortran DLLs and compiler executables are absent. NumPy's complete composite notice/GCC exception already ships. Exact executed GCC source/version/eligible-compilation receipt remains required; no blanket GPL application-source obligation is inferred.

Microsoft: no VS/Build Tools instance, standard installation roots or vswhere was discovered; owner reports VS Code only. Installed x64 VC14.51 runtime proves install/use, not distribution entitlement. Microsoft direct REDIST grants are conditional on licensed VS users; app-local and bundled/chained installer distribution both remain conditional. VS2022 Community section4 also permits licensed producers to authorize distributors of their applications: do not incorrectly require every PSF Python recipient to own VS. The official PSF Windows binary build's additional Microsoft conditions are now delivered as a separate full original legal file. They do not automatically prove authority/scope/downstream term compliance for all13 independent wheel/runtime CRTs. Mastixa adds primary functionality, but that alone does not establish eligibility. No CRT is classified illegal merely because evidence is incomplete.

Preferred alternative without a Mastixa direct redistribution grant: recipients independently download/install the official x64 VC14 runtime from Microsoft; Mastixa copies neither its installer nor CRT DLLs. Minimum14.51.36247.0, Installed=1 plus Version/Major/Minor/Bld/Rbld in the proper registry view, skip equal/newer. Microsoft supports `/install /passive /norestart` or `/quiet /norestart`; any licensed future chaining must handle0/3010 and recheck. Chaining is NOT approved now. Current NumPy/Shapely/pyproj dependencies require3 hashed MSVCP names; official central installation does not supply them. A supplier-approved compatible no-CRT wheel/remapping route and focused frozen/clean-Windows validation are required before removing13 DLLs. Current candidate is unchanged and B2 stays blocked.

CRS: the exact unchanged wheel proj.db hash and retained39-table/77707-row source correspondence remain the basis; that comparison is not rerun. Targeted actual authority rows are ESRI6018/NKG75/IGNF2236/IAU_20152643. These counts cover direct auth_name rows, not all dependent cross-authority rows. Input/generator hashes and each upstream customization statement are retained. The database is mechanically imported AND augmented/customized upstream, not an unmodified original EPSG dataset; Mastixa neither subsets nor edits it. Besides900913 alias and unit short names, upstream updates interpolation CRS and EPSG1312/1462 accuracy. Complete allowed-modification/numerical-equivalence closure is still required. IOGP ownership and full EPSG terms are delivered; PROJ MIT alone does not waive conditions. Esri4 transformation/usage discrepancies and exact NKG member/parameter derivation remain. IGN2020-566 general open-data decision does not prove all exact historical IGNF3.1.0/third-party input rights. IAU publisher page is not an adaptation grant for the generator CSV; ITRF/init rights remain unresolved. No external grid payload is introduced.

B4 source review: build-time supplier/TLS/legal checks remain intact. Normal startup contains no installed-library signature/hash enforcement. Updater hashes downloaded installer bytes; Inno `[Files]` copies recursively with ignoreversion, so explicit update/repair overwrites recipient replacement DLLs. Close the app, preserve a writable onedir copy or back up replacements, install the update explicitly, then reapply a coherent ABI-compatible set. Qt/PySide DLLs belong in `_internal/PySide6`, Shiboken runtime in `_internal/shiboken6`, wheel-renamed GEOS3.13.1 and dependencies in `_internal/Shapely.libs`; preserve generated wrapper ABI/exports and exact loader/import naming. Run native load/startup/input/PDF/GIS checks on a synthetic profile. No secret signature or unsupported installation hack is required by the current design. Retained SDK26 smoke only proves official-library substitution; it is not a usable differently built modified-library receipt. Full QtPdf/binding/GEOS/GCC executed build/patch/toolchain and reproducible generator materials remain missing. No security guard needs weakening based on this source review.

New required rights/source files necessitate a narrow deterministic source snapshot refresh; preserve the old741-file archive/receipt unchanged. Matching upstream archives stay outside the repository, indexed by exact hashes and retained source/build/patch/license materials while binaries are available and at least5 years after last distribution. No public source offer or final binary/source binding exists.

Primary Microsoft references: [redistribution guidance](https://learn.microsoft.com/en-us/cpp/windows/redistributing-visual-cpp-files), [2026 REDIST](https://learn.microsoft.com/en-us/visualstudio/releases/2026/redistribution), [VS2022 Community original terms](https://visualstudio.microsoft.com/wp-content/uploads/2021/11/Visual-Studio-2022-Community-License-EN.docx), [standalone runtime terms](https://visualstudio.microsoft.com/wp-content/uploads/2025/10/Visual-C-V14-License-Redistributable_and_Runtime_ENU.docx). Exact Qt/OpenBLAS/CRS source URLs, archive hashes and primary receipts: `windows-external-rights-closure.json` and sibling `WindowsExternalRightsEvidence`.

Final pre-RC preflight **NOT RUN**: B1-B4 are not all PASS. `native_notices_complete=false`, `corresponding_source_ready=false`. RC may not be built. Next owner action: choose a substantiated supplier/direct Microsoft grant route or the qualified no-CRT/user-installed prerequisite route; obtain the exact remaining QtPdf/binding/GCC/GEOS producer/generator/replacement materials and CRS/EPSG rights/derivation evidence. A compiler license installation alone will not close B1/B3/B4.

Future artifact-build owner requirement:

The owner explicitly authorizes temporary Administrator PowerShell access solely for management of the Bitdefender exclusion required during the future RC build.

For the future artifact build:

1. Identify the ACTUAL PyInstaller/Inno Setup build/work/output directory.
2. Do NOT create or rename a folder to `PROSORINA`.
3. Temporarily exclude the entire real build/work/output directory from Bitdefender for build/packaging/artifact validation.
4. Prefer a supported Bitdefender CLI/API/policy mechanism if available.
5. Administrator PowerShell is explicitly authorized only for this temporary exclusion task.
6. Do NOT exclude repository root, user profile, entire drive or unrelated folders.
7. Do NOT disable Bitdefender globally.
8. Do NOT use undocumented registry hacks.
9. Record the exact exclusion added.
10. After artifact build and validation, REMOVE the temporary exclusion and verify removal.

If Bitdefender cannot be managed through a supported local interface: STOP before the RC build. Present the exact folder path the owner must manually exclude. Wait indefinitely for explicit owner confirmation. No countdown. No timeout. No auto-continue. Continue only after the owner explicitly confirms OK/Done/Continue.

This is mandatory for the future artifact-build batch. No Bitdefender setting is changed now. Current script defaults are `Mastixa-Icon-Diagnosis/build`, `Mastixa-Icon-Diagnosis/dist/MastixaManager` and `Mastixa-Icon-Diagnosis/dist/installer` (or an explicit InstallerOutputDir). The future batch must resolve its actual paths and any Inno temporary compiler output; it must not substitute the repository root or invent a single encompassing directory.
