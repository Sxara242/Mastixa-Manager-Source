> Retained historical engineering record, sanitized for public review.
> Current status: [RELEASE_STATUS.md](RELEASE_STATUS.md). This record does not
> establish approval of the current source or a new binary release. Local-only
> receipt paths refer to privately retained evidence, absent from this snapshot.

# Current candidate disposition — 2026-10-09

**READY TO BUILD WINDOWS 1.0.0-rc.2 CANDIDATE** after source fix batch #1.
The rc.1 build/artifact validation below remains PASS and historical. Subsequent
owner acceptance found FIX 1–11 defects, including MUST-FIX lock/correction defects;
rc.1 is not the final accepted Windows v1 candidate. All rc.1 artifacts and original
candidate evidence remain immutable; 566 dist hashes match the batch baseline.

No rc.1 rebuild/overwrite and no rc.2 build was performed. Product behavior changed,
so a new candidate is required. Current source/package version inputs still describe
rc.1: a separately authorized next build must first set consistent rc.2 metadata and
distinct output identities, freshly bind the changed source, and qualify the affected
frozen behavior. No previous source-overlay record certifies these unbuilt changes.
168 distinct focused source tests and native Windows routes PASS; detailed scope,
validation and exact files: [WINDOWS_RC_OWNER_FIX_BATCH1.md](WINDOWS_RC_OWNER_FIX_BATCH1.md).

Owner install/recovery/persistence/GIS/updater/legal and calculation/export PASS
results remain retained; final owner acceptance awaits rc.2. Legal/package/native
supplier qualification and source-retention inputs are unchanged. Issue #1 OPEN;
no commit/push/tag/upload/publication. All following rc.1 build details and earlier
pending-owner wording describe the retained historical checkpoint.

---

# Windows 1.0.0-rc.1 candidate build record — 2026-10-08

**WINDOWS 1.0.0-rc.1 CANDIDATE BUILT — OWNER ACCEPTANCE REQUIRED**
RELEASE-INFRA / DESKTOP. Actual candidate build succeeded; final acceptance follows the gate table below.
This record supersedes the earlier manual Bitdefender prebuild stop. Historical handoff entries are preserved.
Owner acceptance may begin: **YES**. Owner acceptance itself is **NOT PERFORMED / PENDING**.

Approved dirty worktree: `<WORKSPACE>\Mastixa-Icon-Diagnosis`; branch `icon-runtime-qa-final`; HEAD `0a0031cf8ea20b2956944bf8468da9d647701237`.
Protected original `MastixaManager` and its dirty PNG/backup state are preserved.
Target `1.0.0-rc.1`, channel `rc`, `AGPL-3.0-only`; both executables UNSIGNED.

## Actual build

Ordinary Windows user, no Administrator build. Start `2026-10-08T18:51:16.3421621Z`; finish `2026-10-08T18:53:31.1740185Z`; recipe exit 0.
Python 3.14.8, PyInstaller 6.22.3, hooks-contrib 2026.7, Inno Setup 6.7.3.
Command executed from the approved checkout:

```powershell
$env:PYINSTALLER_CONFIG_DIR = '<WORKSPACE>\Mastixa-Icon-Diagnosis\build\MastixaManager'
$env:TEMP = '<WORKSPACE>\Mastixa-Icon-Diagnosis\build\MastixaManager'
$env:TMP = $env:TEMP
$env:LOCALAPPDATA = '<USER_HOME>\AppData\Local'
& .\packaging\build_release.ps1 -PythonPath '<WORKSPACE>\WindowsReleaseSuppliers\build-venv\Scripts\python.exe'
```

Normal recipe `--clean/--noconfirm` recreated only verified generated `build\MastixaManager` and `dist\MastixaManager` paths.
No source/untracked cleanup; no historical alpha installer files manually removed. Inno output/intermediates are `dist\installer`.
PyInstaller cache is inside `build\MastixaManager\pyinstaller`; TEMP/TMP confined to the same actual work directory.
Inno compiler `<USER_HOME>\AppData\Local\Programs\Inno Setup 6\ISCC.exe`.
Build transcript/start/finish and native build logs are retained under `<WORKSPACE>\WindowsRcCandidateEvidence` and the normal generated build/output directories.

## Bitdefender

Consumer 27.0.63.360; WSC registration and eight running services checked before build.
No supported automated exclusion method was identified. Manual owner flow, no protection disabled or undocumented registry method.
Explicit owner OK confirmed these three temporary Antivirus exclusions active before starting the recipe:

- `<WORKSPACE>\Mastixa-Icon-Diagnosis\build\MastixaManager`
- `<WORKSPACE>\Mastixa-Icon-Diagnosis\dist\MastixaManager`
- `<WORKSPACE>\Mastixa-Icon-Diagnosis\dist\installer`

After successful build/static validation, the owner explicitly confirmed all three removed and absent from the list,
then scanned the frozen application folder and installer with Bitdefender: **no threats found**.
Removal/scan record timestamp `2026-10-08T20:06:08.8658675Z` is the evidence write time; exact user action time was not independently observed.
Activation/removal/scan are owner-confirmed, not independently inspected through the security UI.
No public malware scanner upload or external transfer.

## Exact artifacts

| Artifact | Full path | Bytes | PE / version / signing |
| --- | --- | ---: | --- |
| Frozen application | `<WORKSPACE>\Mastixa-Icon-Diagnosis\dist\MastixaManager\MastixaManager.exe` | 10,740,816 | x64; File/ProductVersion `1.0.0-rc.1`; UNSIGNED |
| Installer | `<WORKSPACE>\Mastixa-Icon-Diagnosis\dist\installer\MastixaManager-1.0.0-rc.1-Setup.exe` | 54,308,871 | x86 Inno loader installs x64 application; numeric File/ProductVersion `1.0.0.1`, visible AppVersion `1.0.0-rc.1`; UNSIGNED |

Application SHA-256: `edfe925e40d648ee1e95a51421b52dc1a10b84b4ec234b313fb9429a0e6c0619`.
Installer SHA-256: `f96b20fbad16aad79f50398b000fe9e7dd6c0ac1715332bee54e55e44ba9bc47`.
All 559 payload files recorded; 101 native dependencies match retained qualified hashes/imports exactly.
See `windows-rc-candidate-artifacts.json` for the native and included notices/license inventory.

External SBOM companion: `<WORKSPACE>\Mastixa-Icon-Diagnosis\dist\installer\MastixaManager-1.0.0-rc.1.sbom.cdx.json`.
SHA-256 `33c15000d0917921af7915a35ef0f0900321bae07375d1abd33e685e5bf8ce99`; same 140 components; actual EXE/installer hashes bound in metadata.
Normal spec does not embed SBOM. Historical prebuild-status text in retained materials is superseded by this actual-artifact association.
Generated `base_library.zip` changed as expected; all 155 modules match locked CPython 3.14.8 source.
All 111 application PYZ modules plus `main` match current sources compiled with the recipe's optimize=1.

New local source overlay: `<WORKSPACE>\WindowsRcCandidateEvidence\MastixaManager-1.0.0-rc.1-current-build-source-overlay.zip`; 28,876 bytes;
SHA-256 `adda9feeeca2af76883f71b1a8488ba81f5ca1eb5fc65a052842cc990ee7ba4e`.
Retained base identifier `MastixaManager-1.0.0-rc.1-Windows-source-candidate.zip`, SHA-256
`34cf3b4007a3554a13aa7a71833ab589bc5e6a8092cf13cea4df54c259a2aefb`, plus six retained overlays in recorded order and this new 8-file hardening overlay reproduce 676 current source/input files.
Nothing overwrites the earlier archives. Local retention has no public source-access/publication claim;
historical source/document paths need the already-documented publication curation before a separately authorized distribution.
Postbuild evidence documents are outside the frozen payload and are not represented as prebuild source inputs.

## Acceptance evidence

| Gate | Result and basis |
| --- | --- |
| Build | PASS: normal release recipe, frozen application + Inno installer + checksums |
| Bitdefender | PASS: manual active/removal owner confirmation and post-removal scan no threats; no independent security UI inspection |
| Installer | PASS: native license/title preview; clean install, repair, actual installed EXE, uninstall/reinstall/uninstall; all payload hashes match; original install/preferences/shortcuts unchanged |
| Version/channel/signing | PASS: 1.0.0-rc.1 / rc / AGPL-3.0-only / UNSIGNED |
| Native frozen smoke | PASS for startup, seven named pages, native text input, light and persisted dark startup, backup/restore/profile export, annual PDF export, GIS import, bundled NumPy/Shapely/pyproj loads, local updater UI and clean shutdown |
| PDF invoice preview | NOT APPLICABLE FOR WINDOWS v1 — PDF primitive PASS; no RC blocker per explicit owner clarification |
| Resource hardening | PASS: retained 268 focused Windows tests; all current application modules match candidate; 16 focused tests executed using candidate bytecode/extensions under matching supplier host; actual EXE backup/restore/export and shutdown pass |
| Warnings/lifecycle | PASS: observed 0 ResourceWarning, 0 RuntimeWarning, 0 Qt lifecycle warnings in named native/installed/probe logs |
| EPSG | PASS: locked derived artifact; supplier unchanged; 1312/1462/7001 attribution; 900913 rules; ranking and unrelated metadata unchanged |
| Native dependencies | PASS: exact retained 101 dependency hashes/imports; no new dependency, VirtualKeyboard, Mesa, old OpenSSL or bundled Microsoft CRT; relevant actual process modules bundle-local |
| SBOM/legal | PASS: 140 retained components reconciled; candidate hash-bound external SBOM companion; required retained notices/source/replacement materials unchanged |
| Updater | PASS: actual EXE local staging check; candidate-bytecode invalid-certificate/SHA/retry/release-note/late-window-result probes PASS; loopback inert payload only, no production feed or URL |
| Publish safety | PASS for binary payload: no owner DB/profile/records/backups/credentials/logs/screenshots/evidence/private paths found by membership/hash/marker checks |
| Source retention | PASS local artifact binding: 676 current source/input files reproduced by retained base + overlays + new 8-file overlay; no publication or public source-access claim |

Native UI used only a fresh synthetic `MASTIXA_DATA_HOME` under `<WORKSPACE>\WindowsRcCandidateEvidence\native-rc`; no active owner profile copy.
Actual installer tests used isolated `<WORKSPACE>\WindowsRcCandidateEvidence\install-rc`; existing preference key/shortcuts were reversibly protected and restored identically.
All 559 installed payload hashes matched on clean install, repair and reinstall. Synthetic app data survived uninstall/reinstall.
Compatible Qt6Core copy with an inert marker demonstrated overwrite by repair, preservation outside installation and reapplication.
This checks documented replacement behavior, not a full rebuilt Qt library or pristine-machine dependency test.
The existing machine's qualified VC Redist prerequisite was accepted; machine prerequisites were not removed to simulate absence.

Actual EXE annual PDF export: 23,698 bytes; profile export: 6,666 bytes.
Manual backup/restore succeeded, including pre-restore safety backup. Typed field survived restore and restart.
GIS import displayed EPSG:4326, four vertices, 9749.03 m² / 397.66 m, stored a visible offline polygon.
Actual process load paths include bundled NumPy/Shapely/PROJ, qpdf.dll and Qt6Pdf.dll.
Light startup and persisted dark startup passed. Two subsequently parent-tracked native UI shutdowns returned exit 0;
the earlier normally closed GIS run logged shutdown but attached .NET observer did not expose an exit code.
An earlier input-interrupted process is explicitly excluded from clean shutdown proof.

Hosted probes use **candidate PYZ bytecode and bundled extensions/data** under matching supplier Python 3.14.8,
with bundle DLL/plugin search, not application source imports. They supplement the separately tested real EXE.
They cover 16 focused failure/lifetime tests, late updater result after deleted Qt windows, cleanup/rollback/recovery,
OpenSSL 3.5.9 for Python and Qt, invalid certificate rejection through existing fetch path, SHA/retry/release-note rules,
and bundled QPixmap PDF rendering. Local loopback server/inert bytes only, never a public feed or executed update payload.
They do not claim these failure injections were driven through the real frozen EXE UI.

EPSG derived DB SHA-256 `590adc683437a59896e8841255129b572b082008eebf1c0d5225e6c5e207c064`;
supplier input unchanged at `528b9763b57e85ee78f6f30478ef0494902320f1d71d1564bf0d7ec4f30cc002`.
Only the qualified three transformation remarks, PROJ alias authority and associated alias usage row differ;
operation rankings for the four retained sample areas and all unrelated table data match supplier behavior.
No EPSG legal reassessment, native supplier qualification, old 99-scenario audit, UI/performance or Android rerun.

Invoice classification: **NOT APPLICABLE FOR WINDOWS v1 — PDF primitive PASS**. Παραστατικά / Invoices are intentionally `Υπό κατασκευή` and outside Windows v1 functional scope. End-to-end invoice UI preview is not a release requirement for this RC.
Primitive result: `PASS: candidate QPixmap/qpdf/Qt6Pdf rendered real EXE-exported synthetic PDF at 842x595`.
Decision: **Owner explicitly confirms Invoices are outside Windows v1 functional scope; bundled PDF primitive PASS is sufficient and invoice UI preview is not an RC requirement.** No product code or invoice functionality changed.
Owner clarification recorded 2026-10-08T20:33:06.806234+00:00; this is scope clarification, not final owner acceptance.

## Preservation and next step

No production source/test/dependency/packaging/legal fix made during build. Only external validation harness corrections,
postbuild evidence documents, external SBOM companion and local source overlay were produced.
Final `candidate-preservation.json` records all original-file hashes, both HEADs, exact Git status/counts and `git diff --check`.
Build-validation snapshot of approved worktree: 57 tracked modified, 323 untracked, 0 staged;
986 original file hashes compared, only permitted postbuild docs differ. Protected original: 32 modified PNGs,
32 untracked backup files, 0 staged; all 515 original hashes and exact status unchanged. `git diff --check` PASS.
Retained B1–B5/EPSG PASS and 268 focused hardening tests remain unchanged; build alone does not grant owner acceptance.

Next owner action: Owner executes WINDOWS_RC_OWNER_ACCEPTANCE.md against this exact installed RC and records an explicit acceptance or rejection. Owner acceptance has not been performed; issue #1 remains OPEN.
Issue #1 remains **OPEN**. No commit/push/tag/sign/publication/upload/external issue write.
This is an unsigned RC candidate; no final `1.0.0` release or distribution approval is claimed.

Raw and machine-readable records: `<WORKSPACE>\WindowsRcCandidateEvidence`; checksum companion `windows-rc-candidate-SHA256SUMS.txt`.
Installer, frozen smoke, SBOM, EPSG, publish-safety and source-retention records are adjacent `windows-rc-candidate-*.json` files.

Owner clarification changes documentation only; no rebuild or test rerun. Existing binary/payload hashes,
SBOM/legal/EPSG/source-retention/checksum results and Bitdefender post-build evidence remain unchanged.
Original raw evidence under WindowsRcCandidateEvidence is retained byte-for-byte; its earlier BLOCKED
classification predates this owner scope clarification. Current classification is this record and
windows-rc-candidate-validation.json. Owner checklist: WINDOWS_RC_OWNER_ACCEPTANCE.md.
