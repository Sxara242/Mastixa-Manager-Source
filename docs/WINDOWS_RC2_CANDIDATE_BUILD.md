> Retained historical engineering record, sanitized for public review.
> Current status: [RELEASE_STATUS.md](RELEASE_STATUS.md). This record does not
> establish approval of the current source or a new binary release. Local-only
> receipt paths refer to privately retained evidence, absent from this snapshot.

# Windows 1.0.0-rc.2 preparation — 2026-10-09

**BLOCKED DURING WINDOWS 1.0.0-rc.2 CANDIDATE BUILD**

RELEASE-INFRA / DESKTOP. STOPPED BEFORE BUILD: manual Bitdefender exception
confirmation is required under the owner's explicit instruction. No PyInstaller,
Inno compiler, frozen rc.2 launch or installer validation has run. Source readiness
remains READY TO BUILD; this is an antivirus workflow hold, not a reopened product
or legal blocker. Final owner acceptance is pending and has not been performed.

## Retained state and preparation

Approved dirty checkout: `<WORKSPACE>\Mastixa-Icon-Diagnosis`,
branch `icon-runtime-qa-final`, HEAD `0a0031cf8ea20b2956944bf8468da9d647701237`.
All 44 FIX 1–11 checkpoint hashes matched at entry. Retained 168 distinct tests /
18 modules, 55/55 stock recheck, 5/5 closure recheck and warning results are reused;
no completed fix or historical full audit was repeated. No product behavior changed.

All 566 rc.1 dist hashes, all 515 protected-checkout hashes and exact protected Git
status matched. 157 files under historical rc.1/Owner Fix Batch #1 evidence folders
were separately hashed before preparation and remain immutable. Original candidate
JSON/checksums, source archives and rc.1 build/acceptance documents remain historical.
No reset, clean, revert, branch switch, staging, commit, push, tag, upload, publication
or issue write. Issue #1 remains OPEN.

Target app/config/feed/installer versions are now `1.0.0-rc.2`, channel `rc`, license
`AGPL-3.0-only`, signing intent `UNSIGNED`; numeric PE version will be `1.0.0.2`.
README/CI metadata and affected version assertions match. Android identity unchanged.
The ordinary recipe now accepts explicit PyInstaller work/dist paths and passes the
selected bundle to Inno through `MyAppSourceDir`; existing CI default directories are
preserved. The guarded rc.2 wrapper supplies all three isolated paths below.

25 metadata/updater/legal UI tests PASS; 7 directly affected packaging contracts
PASS; 0 ResourceWarning, 0 RuntimeWarning, 0 Qt lifecycle messages/exceptions.
One old synthetic legal/privacy fixture lacked the separately required EPSG database;
its EPSG-only dependency is now isolated. Production EPSG verification is unchanged;
real rc.2 EPSG artifact validation remains mandatory. Initial failed run is retained.
No newly claimed frozen, installer, pristine-machine or owner acceptance result.

B1/B4 legal PASS with optional audit/reproduction gaps and B2/B3/B5 COMPLETE PASS
remain retained. EPSG interpretation, Microsoft prerequisite/zero-shipment strategy,
OpenSSL/Mesa inputs and VirtualKeyboard exclusion are unchanged. Current source
preflight checks metadata/legal selection and locked supplier inputs; it does not
redo supplier/legal qualification.

## Exact candidate paths

Only these three empty directories were created for browsing/manual setup:

- `<WORKSPACE>\Mastixa-Icon-Diagnosis\build\1.0.0-rc.2\MastixaManager`
- `<WORKSPACE>\Mastixa-Icon-Diagnosis\dist\1.0.0-rc.2\MastixaManager`
- `<WORKSPACE>\Mastixa-Icon-Diagnosis\dist\1.0.0-rc.2\installer`

Expected frozen EXE:
`<WORKSPACE>\Mastixa-Icon-Diagnosis\dist\1.0.0-rc.2\MastixaManager\MastixaManager.exe`.
Expected installer:
`<WORKSPACE>\Mastixa-Icon-Diagnosis\dist\1.0.0-rc.2\installer\MastixaManager-1.0.0-rc.2-Setup.exe`.
Neither exists; byte sizes, SHA-256, PE architecture and signature results are pending.
Evidence: `<WORKSPACE>\WindowsRc2CandidateEvidence`.

## Required manual Bitdefender step

Installed consumer Total Security identifies version `27.0.63.360`. No supported
automated consumer exception interface was identified. CIM/WSC/service inspection
is unavailable in this sandbox; current protection/exceptions are not claimed verified.
The prior rc.1 confirmations applied to different paths and do not authorize continuing
through this explicitly required new manual-confirmation gate.

Use Protection → Antivirus → Open → Settings → Manage Exceptions → Add an Exception.
Add each of the three exact paths above, enable Antivirus for each, Save, and verify
all three entries are listed. Official instructions:
[Bitdefender folder exceptions](https://www.bitdefender.com/consumer/support/answer/13427/).
No repository/profile/drive exclusion, extension wildcard, global disable or registry
hack. The agent added no exclusions. Explicit owner OK/Done/Continue confirming these
three entries active is required; wait indefinitely without automatic continuation.

After build and validation, remove exactly these temporary entries, verify absence,
and scan the frozen folder and installer where supported. Owner confirmation must
be labelled as such if independent security UI inspection remains unavailable.

## Prepared command — not executed

The guarded wrapper rejects an invocation without explicit confirmation; the switch
may only be supplied after the owner confirms the three entries in chat.

```powershell
& '<WORKSPACE>\WindowsRc2CandidateEvidence\build-run.ps1' -OwnerConfirmedExactExclusions
```

The wrapper checks ordinary-user privileges, HEAD, all prepared overlay hashes,
historical preservation and directory containment/reparse points. It confines
TEMP/TMP/PyInstaller configuration/cache to the exact rc.2 work directory and runs:

```powershell
& .\packaging\build_release.ps1 `
  -PythonPath '<WORKSPACE>\WindowsReleaseSuppliers\build-venv\Scripts\python.exe' `
  -PyInstallerWorkPath '<WORKSPACE>\Mastixa-Icon-Diagnosis\build\1.0.0-rc.2' `
  -PyInstallerDistPath '<WORKSPACE>\Mastixa-Icon-Diagnosis\dist\1.0.0-rc.2' `
  -InstallerOutputDir '<WORKSPACE>\Mastixa-Icon-Diagnosis\dist\1.0.0-rc.2\installer'
```

## Required postbuild validation — all NOT RUN

1. Actual frozen startup; version/channel; byte sizes, hashes, architecture/signing.
2. Isolated install/repair/uninstall/reinstall, synthetic existing data persistence.
3. Frozen UI; Production/Sales/Warehouse stock; year defaults/filters/management.
4. Locked-year CRUD; reasoned correction/navigation/exits; numeric input.
5. Annual entry year and own-unit weighted average export; backup/restore/safety/export.
6. GIS/EPSG; local staging feed; shutdown/restart; warning/lifecycle accounting.
7. Native hashes/imports/count reconciliation; qualified dependency/absence policies.
8. Actual hash-bound SBOM/legal/source overlay/source-retention and publish safety.
9. Bitdefender temporary exception removal verification and supported postbuild scan.

Use synthetic QA data and preserve production installation/preferences/shortcuts.
No historic 99-scenario rerun unless a material artifact reason appears. No owner
acceptance on the owner's behalf. Owner acceptance checklist:
[WINDOWS_RC2_OWNER_ACCEPTANCE.md](WINDOWS_RC2_OWNER_ACCEPTANCE.md).

Machine checkpoint: external `prebuild-record.json`, `approved-overlay.json`,
`baseline.json`, `preservation.json`, metadata/packaging logs and guarded build script.
No artifact/source/public-access completion is inferred from preflight readiness.
