> Retained historical engineering record, sanitized for public review.
> Current status: [RELEASE_STATUS.md](RELEASE_STATUS.md). This record does not
> establish approval of the current source or a new binary release. Local-only
> receipt paths refer to privately retained evidence, absent from this snapshot.

# Owner result and fix batch #1 — 2026-10-09

The rc.1 build/artifact validation **PASSED**. Subsequent owner acceptance found
FIX 1–11 product/UX defects, including release-blocking locked-year update bypass
and unusable correction editing. **rc.1 is not the accepted final Windows v1
candidate.** Preserve its binaries as immutable historical candidate artifacts.

Owner-recorded PASS results, retained without reopening unrelated gates:

- Install / launch and basic navigation.
- Settings / AGPL / source access.
- Production save; Sales arithmetic and production-derived stock; Expenses create.
- Backup; Restore; automatic pre-restore safety backup; Profile Export.
- Annual Report arithmetic and PDF export.
- GIS EPSG:2100 and polygon persistence.
- Local staging updater feed.
- Shutdown/restart, repair and uninstall/reinstall persistence.

FIX 1–11 source changes are implemented; 168 distinct focused tests across 18
modules PASS, including 0 ResourceWarning/RuntimeWarning and Qt lifecycle failures/
exceptions. Native Windows source interaction and actual PDF layout checks PASS.
Exact mapping, tests, files, warning caveats and results:
[WINDOWS_RC_OWNER_FIX_BATCH1.md](WINDOWS_RC_OWNER_FIX_BATCH1.md).

Current source gate: **READY TO BUILD WINDOWS 1.0.0-rc.2 CANDIDATE**.
No rc.2 build or installer exists from this batch. A new build is required and must
be separately instructed; rc.1 must not be rebuilt/overwritten. Final Windows v1
owner acceptance remains pending on rc.2, with these focused checks:

- [ ] Produced-product Warehouse view: 120 kg − 101 kg = 19 kg; supplies separate; carry-over after year change.
- [ ] Transaction/Report/Calendar defaults, empty managed years and annual KPIs follow working context; master data stays visible.
- [ ] ±1/manual validated year transition; cancellation; lock/read-only refresh.
- [ ] Year Lock defaults to active year and confirms actual selected management year.
- [ ] Locked-year create/edit/delete blocked across dated modules; legitimate correction CRUD works and audit reason persists.
- [ ] Exit correction stays on that locked year; separate return action restores normal active year; banners distinguish both.
- [ ] Numeric first typing 12, decimals/comma/dot, replacement/paste/delete, units and validation.
- [ ] Annual Report entry defaults to active year, preserves manual choice on-page and exports separate weighted own-unit prices with no-sales dash.
- [ ] New candidate identity/source binding and directly affected frozen lifecycle flows qualify successfully.

No agent source test constitutes owner acceptance of a frozen rc.2. Existing
passed install/recovery/GIS/updater evidence is retained; repeat only candidate-bound
or affected checks as required by the subsequent build. Date default `09/10/26`,
custom unit `2τεμάχια2`, cross-year master data and mixed-unit overall average —
are intentional behavior, not defects. Issue #1 remains OPEN; no commit/push/tag/
upload/publication. The original rc.1 checklist below is historical; its initially
unchecked state and pending-owner wording predate the recorded owner results above.

---

# Windows 1.0.0-rc.1 — owner acceptance checklist (historical)

RELEASE-INFRA / DESKTOP. Candidate eligible for owner acceptance; acceptance has
**not** been performed or granted by the agent. All boxes below start unchecked.
Use the actual installed RC executable, not source Python or an older shortcut.

## Exact candidate and test setup

Installer:
`<WORKSPACE>\Mastixa-Icon-Diagnosis\dist\installer\MastixaManager-1.0.0-rc.1-Setup.exe`

Installer SHA-256:
`f96b20fbad16aad79f50398b000fe9e7dd6c0ac1715332bee54e55e44ba9bc47`

Installed `MastixaManager.exe` must match SHA-256:
`edfe925e40d648ee1e95a51421b52dc1a10b84b4ec234b313fb9429a0e6c0619`

The earlier agent validation install was uninstalled after testing. The owner
installs this exact candidate into a test environment and records the installed
path. Keep production installation/data intact: use a separate test environment
or account and a disposable synthetic profile for write/restore/uninstall tests.
Any owner-data trial uses a backed-up QA copy, never the sole live profile.
Keep Bitdefender in its normal state with the temporary build exclusions removed.

## MUST PASS before acceptance — owner executes

- [ ] **Correct installation and identity.** Install the exact candidate as an
  ordinary user on x64 Windows with the required official x64 VC Redist
  `>=14.51.36247.0`. Installer/app show `1.0.0-rc.1`; channel is `rc`;
  AGPL/legal materials are accessible. Verify the installed EXE hash and launch
  it from the recorded test path. No quarantine, missing DLL, crash or wrong
  executable. The Inno loader's numeric PE version `1.0.0.1` is expected.
- [ ] **Startup and navigation.** Open Dashboard, Fields, Money, Producer,
  Production, Reports/Annual Report and Settings. Visible contents finish
  painting, controls work, and navigating away/back keeps the correct context.
  Judge usability in the owner's normal window size; record any blocking delay
  or inaccessible control with the page and action that triggered it.
- [ ] **Native input and settings.** Enter Greek/Latin text, dates and numeric
  values in synthetic records; save and reopen them. Switch light/dark and the
  normally used language, then restart: selections persist and cached pages
  display the selected language/theme correctly.
- [ ] **Core records and totals.** In the synthetic profile, create a field,
  product/stock, production entry, expense and sale. For a product-stock test,
  select Product sale and a product. Check the expected stock, money totals and
  annual report; edits and persistence must not lose or mix records.
- [ ] **Year lock and correction.** Switch years and cancel a pending switch
  once: year, draft and page remain unchanged. In a locked test year, writes are
  blocked. Enter correction, cancel/confirm return and finish correction:
  banners and controls immediately match the state, including cached pages.
- [ ] **Backup, restore and profile export.** Back up the synthetic profile,
  make a recognizable change, restore the backup and confirm the expected data
  and pre-restore safety backup. Export the profile successfully. A failed or
  cancelled operation must leave the working profile usable and intact.
- [ ] **Annual-report PDF export.** Export a report from the installed EXE,
  open the resulting PDF and check text, totals and layout. Invoice UI preview
  is excluded from this checklist; the bundled PDF primitive already passed.
- [ ] **GIS.** Import a small synthetic GeoJSON/WGS84 boundary with no network
  basemap; confirm CRS, visible polygon, sensible area/perimeter and persistence
  after reopening. Existing artifact EPSG/NumPy/Shapely/pyproj checks are retained;
  the owner does not need to repeat the full EPSG forensic matrix.
- [ ] **Local staging updater.** In Settings → Updates, confirm installed
  `1.0.0-rc.1` / `rc`, local staging notice and successful latest-version result.
  No production feed, public download or installation is part of this test.
- [ ] **Shutdown and installation lifecycle.** Close normally, restart and
  verify saved data/settings. Check diagnostics for crashes, ResourceWarning,
  RuntimeWarning or Qt lifecycle errors. In the isolated environment, repair,
  uninstall without data purge and reinstall: application starts again and the
  retained test data remains usable. Production data stays unchanged.

Acceptance requires every applicable MUST PASS item to pass and no unresolved
data-integrity, crash, security-validation or unusable-workflow defect. A failure
is recorded as a concrete blocker with steps, expected/actual result and relevant
diagnostics. The owner explicitly accepts or rejects this exact hash pair after
the checks; a scope clarification alone does not grant acceptance.

## Informational / known non-blocking follow-ups

- **NOT APPLICABLE FOR WINDOWS v1 — PDF primitive PASS.** The owner explicitly
  excludes Παραστατικά / Invoices from Windows v1 functional scope. Its intentional
  `Υπό κατασκευή` state and unavailable invoice UI preview are not RC blockers.
- This RC is **UNSIGNED**. Numeric Inno metadata and an x86 installer loader for
  the x64 application are expected; the product/version displayed is the RC.
- Cosmetic issues that leave the workflow usable are recorded as
  **UI/POLISH FOLLOW-UP**. The earlier automated smoke does not constitute owner
  approval of perceived responsiveness or the owner's normal display setup.
- B1 audit / B4 full producer-reproduction details remain documented optional
  follow-ups; retained legal/source-material gates passed. No full/bit-identical
  supplier rebuild or pristine-machine result is newly claimed here.
- TLS/SHA/retry/deleted-window failure probes used candidate bytecode and bundled
  libraries under the matching supplier host. They supplement actual installed
  EXE smoke; do not repeat them or contact a production feed for owner acceptance.
- Final signing, curated public source access, publication and issue #1 closure
  require separate authorized steps. Issue #1 stays OPEN throughout this checklist.

## Post-v1 items

- Invoice functionality: import, OCR, editing and financial posting.
- An invoice-preview UI workflow when the invoice feature is introduced under a
  separate authorized scope, with its own functional acceptance checks.

## Owner result — unfilled

- Test date / Windows environment / installed path:
- Candidate installer and installed EXE hashes verified:
- MUST PASS results and any blockers:
- Informational follow-ups:
- Owner decision: **PENDING**.

Build/artifact proof: `WINDOWS_RC_CANDIDATE_BUILD.md` and adjacent
`windows-rc-candidate-*.json`. This checklist changes no product or payload.
