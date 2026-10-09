> Retained historical engineering record, sanitized for public review.
> Current status: [RELEASE_STATUS.md](RELEASE_STATUS.md). This record does not
> establish approval of the current source or a new binary release. Local-only
> receipt paths refer to privately retained evidence, absent from this snapshot.

# Windows v1 owner acceptance fix batch #1 — 2026-10-09

**READY TO BUILD WINDOWS 1.0.0-rc.2 CANDIDATE**

DESKTOP / RELEASE-INFRA, Windows only. This is source-fix readiness, not artifact
qualification or final owner acceptance. No rc.2 build was run. The rc.1 application,
installer and retained build evidence remain immutable historical candidate artifacts.
GitHub issue #1 remains OPEN; no commit, push, branch switch, tag, upload or publication.

## Owner decision and retained passes

The actual `1.0.0-rc.1` build/artifact validation passed. Subsequent owner acceptance
found the FIX 1–11 defects below, including release-blocking lock/correction defects;
rc.1 is **not the final accepted Windows v1 candidate**.

Preserve the owner's PASS evidence for install/launch, basic navigation, Settings/
AGPL/source access, Production save, Sales calculations, production-derived sales
stock, Expenses create, Backup, Restore, automatic pre-restore safety backup, Profile
Export, Annual Report calculations/PDF export, GIS EPSG:2100/polygon persistence,
local staging updater, shutdown/restart, repair and uninstall/reinstall persistence.
Only directly affected source behavior was exercised in this batch. The historic
99-scenario audit, packaging, legal/source qualification and native supplier gates
were not rerun. B1–B5, EPSG, OpenSSL, Mesa, CRT prerequisite and retention inputs are
byte-unchanged from the batch baseline.

## FIX mapping and verification

| FIX | Implemented behavior | Focused result |
| --- | --- | --- |
| 1 | Warehouse has a separate read-only produced-product section: product, own unit, total production, sold and physical available stock. Uses existing authoritative Production/Sales identity and quantity functions; supply items remain separate. | PASS: 120 kg produced − 101 kg sold = 19 kg across year changes; independent supply stock remains 5. |
| 2 | Dated pages default to the effective working year on entry/context change. Production and maintenance history now have year filters; sales annual KPIs follow the selected year, while physical availability remains all-time. Master pages/sections are unfiltered. | PASS: 16 filter routes; fields, products, links, workers, machinery, partners, producer and supplies survive year changes. |
| 3 | Shared managed-year population includes normal/effective active years and known transaction/lock years, including empty years; supported All years options remain. | PASS: empty 2025 and managed empty 2024 selectable; context change selects empty 2023. |
| 4 | Small −1/+1 controls call the existing validated/confirmed year transition, preserving manual input and Μετάβαση. Bounds/cancellation are respected; no extra year metadata is created. | PASS: unit interactions and native Windows −1 transition. |
| 5 | Year Lock defaults to normal active year on entry/context change, preserves manual selection on the same page, identifies differing management year, and confirms the selected year. | PASS: selection and dialog content checks. |
| 6 | Writable Database connections install common TEMP SQLite guards for INSERT/UPDATE/DELETE, checking both OLD and NEW dated years, including indirect expense/inventory projections. Query helpers are read-only. | PASS: every common dated table, raw execute/executemany and transaction writes, cross-year moves and atomic rollback. |
| 7 | Existing process/profile-scoped correction permission is read dynamically by the common guards. Cached transaction controls re-evaluate record/draft years without losing drafts. Physical locks remain set; corrections retain reasons in audit_events. | PASS: cross-module CRUD, reasoned audit, other-year/profile denial, session exit/restart, cached Income/Expenses and native Production correction. |
| 8 | Top action Έξοδος από προσωρινή διόρθωση exits and stays on the correction year in read-only state. Separate Επιστροφή στο ενεργό έτος YEAR exits and returns to the saved normal year. Banners distinguish both years. | PASS: both actions, cancellation and native 2027 normal / 2026 correction route. |
| 9 | Shared amount/quantity/area and direct price/hour/count fields use visual empty placeholders; units are presentation outside focus, first input replaces zero, comma/dot entry preserves bounds/precision. Supply numeric text inputs support empty-as-zero safely. | PASS: first typing 12, decimals, paste, select-all, backspace/delete, suffix, zero, permitted negatives, precision and limits. |
| 10 | Annual Report selects effective active year on entry/context change and preserves manual selection during interaction on that page. | PASS: entry, manual selection, refresh and reopen, including deferred report sections. |
| 11 | Annual exports show each product's weighted revenue/sold average with its own unit; no qualifying sales show —. Mixed-unit aggregate remains — and revenue/net arithmetic is unchanged. | PASS: own-unit 1 €/kg and 2.5 €/piece, no-sales product, single-product case, CSV/XLSX/PDF and visual PDF review. |

The common dated-table audit covers Production, Income, Expenses, declarations,
activities, supply movements, plant protection, labor, planting batches, production
sales, maintenance, plant events, crop tasks, replantings and invoice-document dates.
Invoice UI remains outside Windows v1 scope. TEMP guards do not alter persistent
schema or introduce UDF-dependent triggers into backups/exported databases. Existing
legacy initialization/migration runs retain their separate initialization path.

During native verification an additional pending-construction case was reproduced:
context refresh before Inventory's movement form exists. The shared refresh now waits
for those controls; form construction then applies current lock/correction state.
A dedicated regression verifies this transition. Cached pages and their identity
remain intact; no eager page construction was introduced.

Production correction is also verified before the lazy Sales page has ever opened.
The existing stock-safety check now treats an absent sales table as no sales,
permitting valid Production create/edit/delete without a page-opening dependency.
When sales exist, all existing total/field stock safeguards still apply. This case
was reproduced as one failing test before the narrow fix, then passed both the
transaction interaction test and native Windows route without warming Sales first.

Date default behavior and the deliberately entered custom unit `2τεμάχια2` are
unchanged. Nonempty required scheduling intervals, year selectors, retention counts
and the existing GIS coordinate editor retain their established behavior. No runtime
dependency, packaging input or legal material changed; no Android work was performed.

## Tests added and updated

New `tests/test_windows_owner_fix_batch1.py`: 16 focused tests (including per-page/
per-table subtests) covering all FIX requirements. Added one pending-Inventory-form
regression in `tests/test_staged_construction.py`.

Updated directly affected tests:

- `tests/test_activity_expense_sync.py`: explicitly select fixture years and keep the source profile's annual context correct before its export/import assertion.
- `tests/test_equipment_maintenance_contract.py`, `tests/test_equipment_meter_type_ui_guard.py`: delete fixture pages before removing their temporary database.
- `tests/test_owner_year_acceptance.py`: empty numeric zero and the separate normal-year return action.
- `tests/test_phase16j_year_correction.py`: active-year entry defaults and distinct exit semantics.
- `tests/test_report_consistency.py`, `tests/test_report_quantity_contract.py`: explicitly select All years when testing aggregate arithmetic and the intended fixture year when testing annual rendering.
- `tests/test_staged_construction.py`: active-year entry versus subsequent manual report selection; pending-form context regression.
- `tests/test_year_context_core.py`: explicit old-year selection before editing an older fixture record.

## Exact validation results

**168 distinct focused tests PASS across 18 modules.** No full historic audit.

| Run | Modules | Result |
| --- | --- | --- |
| Owner/year regressions | test_windows_owner_fix_batch1, test_year_context_core, test_owner_year_acceptance, test_phase16j_year_correction | 47 PASS, 83.391 s |
| Reporting and sales stock | test_report_quantity_contract, test_report_consistency, test_sale_sources | 42 PASS, 84.225 s |
| Atomic stores, history and handle lifetime | test_activity_expense_sync, test_inventory_expense_atomicity, test_equipment_maintenance_atomicity, test_planting_history, test_sqlite_resource_lifetime | 40 PASS, 85.742 s |
| Deferred construction, inventory and equipment | test_staged_construction, test_inventory_quality_gate, test_inventory_ledger_contract, test_equipment_maintenance_contract, test_equipment_meter_type_ui_guard, test_alpha2_step3_year_context | 37 PASS, 38.322 s |
| Final check after the pending-form fix, including its new test | Owner/year group plus test_staged_construction, test_inventory_quality_gate, test_inventory_ledger_contract | 70 PASS, 90.792 s |
| Final check after the Production-before-Sales fix, including its new test | test_windows_owner_fix_batch1, test_sale_sources, test_year_context_core | 55 PASS, 82.788 s |
| Resume/closure: only directly affected stock checks | Production-before-Sales correction; Warehouse carry-over/annual KPIs; field-sale production safeguard; transaction stock recheck/rollback; mixed-unit annual carry-over | 5 PASS, 8.622 s |

The final rechecks supersede earlier results for their changed sources. Unchanged
report/store/equipment results are retained. Every final run has **0 ResourceWarning /
RuntimeWarning, 0 Qt lifecycle warnings and 0 Qt Python exceptions**. The harness
records all Qt messages and drains deferred widget deletion before temporary DB
cleanup; it does not filter Python resource warnings. An intentionally unclosed
SQLite connection positive control produces 1 ResourceWarning, confirming detection.

At resume, all 44 batch-owned files matched the last checkpoint hashes. The last
stock-related recheck was already complete (55 PASS); only the five directly
affected stock tests were rerun for closure. All five passed with 0 ResourceWarning,
0 RuntimeWarning, 0 Qt lifecycle warnings and 0 Qt Python exceptions. This is a
repeat subset, so the unique total remains 168, not 173. No completed fix was redone;
only final documentation/evidence was updated after the checkpoint comparison.

Native `QT_QPA_PLATFORM=windows` source run: six real-window routes PASS, including
keyboard/mouse save, cached Production correction, both exit actions, Warehouse,
Annual Report entry and year navigation, light/dark themes; **0 Qt messages / 0
exceptions**. This uses a disposable synthetic profile, not the owner's database
or a rebuilt frozen executable. Screenshots were visually reviewed. Actual PDF
output was rendered with Poppler and both pages visually checked for own-unit
averages, no-sales dash, totals and unclipped layout.

Offscreen logs retain environmental `propagateSizeHints`, font-face and Windows
printer-DC diagnostics where emitted. These are distinct from lifecycle failures;
the actual PDF export/text/layout checks pass. The supplier venv launcher also
prints its pre-existing real-location diagnostic but executes with successful
exit codes. No blanket warning suppression was added to application code.

`git diff --check`: PASS. Changed Python source compilation with SyntaxWarning as
error: **38 files PASS, 0 warnings**. Batch-owned text files have no trailing
whitespace. No pre-existing file deleted.

Reproduction before implementation: three targeted tests produced 20 failed
subtests and 2 errors, covering active-year/empty-filter/zero-editor defects.
Existing lock/correction tests and direct-call owner tests were also identified
before changing enforcement. Retained raw logs show failed diagnostic runs as
well as the final passes; intermediate failures are not final validation results.

Evidence: `<WORKSPACE>\WindowsOwnerFixBatch1Evidence`:
`baseline.json`, `final-preservation.json`, `owner-final.log`, `reports-final.log`,
`stores-final.log`, `staged-final.log`, `final-recheck.log`, `production-final.log`,
`resume-stock-closure.log`,
`validation-summary.json`, `validation-*.json`,
`native-final.log`, `native-flows.json`, native screenshots, PDF/Poppler renderings,
`git-diff-check.log`, and the focused/native/preservation harness scripts.

Commands use the qualified supplier
`<WORKSPACE>\WindowsReleaseSuppliers\build-venv\Scripts\python.exe`
(Python 3.14.8), `QT_QPA_FONTDIR=C:\Windows\Fonts`, disposable `MASTIXA_DATA_HOME`
and TEMP/TMP under the evidence folder. The test runner command is
`python run_focused.py tests.<module> ...` with the exact module groups above and
`QT_QPA_PLATFORM=offscreen`; native routes use `python native_owner_flows.py` with
`QT_QPA_PLATFORM=windows`. Neither command invokes PyInstaller or Inno.

## Exact files changed by this batch

This list compares with the captured dirty baseline, not HEAD. It does not claim
ownership of earlier modifications already present in these files.

Existing application files (26):

```text
app/activities.py
app/annual_report.py
app/annual_report_exports.py
app/crud.py
app/database.py
app/equipment.py
app/farm_calendar.py
app/field_finance.py
app/fields.py
app/inventory.py
app/labor.py
app/locales/en.json
app/money.py
app/plant_protection.py
app/planting_history.py
app/plantings.py
app/production.py
app/product_registry.py
app/reports.py
app/sales.py
app/sales_report.py
app/upload_center.py
app/widgets.py
app/year_context.py
app/year_context_ui.py
app/year_lock_robustness.py
```

New application files (3): `app/numeric_inputs.py`, `app/year_filters.py`,
`app/year_write_policy.py`.

Existing test files (9): the nine filenames listed under Tests added and updated
(the equipment pair counts as two). New test file:
`tests/test_windows_owner_fix_batch1.py`.

Existing documentation files (4): `docs/CODEX_HANDOFF.md`,
`docs/CODEX_PROJECT_CONTEXT.md`, `docs/WINDOWS_RC_CANDIDATE_BUILD.md`,
`docs/WINDOWS_RC_OWNER_ACCEPTANCE.md`. New document:
`docs/WINDOWS_RC_OWNER_FIX_BATCH1.md`. **44 repository files total**.

External evidence scripts/logs/synthetic data are confined to
`WindowsOwnerFixBatch1Evidence`, outside the shipping checkout. Byte hashes for
every batch-owned repository file are recorded in `final-preservation.json`.

## Preservation, Git counts and next gate

Approved HEAD unchanged: `0a0031cf8ea20b2956944bf8468da9d647701237`.
Protected original HEAD unchanged: `b1765241aa18796962f39cdf001ae717f39f6c0a`.
All 998 baseline source/input files accounted for; changes are limited to the
listed batch-owned files. All **515 protected-original hashes** and **566 dist
artifact hashes** match. No legal/package/supplier/source-retention change.

Git porcelain `-uall` file counts: approved checkout **72 modified / 330 untracked /
0 staged / 0 deleted** (baseline 57 / 325 / 0 / 0). Original **32 modified PNG /
32 untracked backup files / 0 staged / 0 deleted**, exact status unchanged.

No unresolved FIX 1–11 issue remains in the focused source validation. These
product behavior changes **require a new candidate build**. rc.1 still contains
the rejected behavior and must not be overwritten/rebuilt. On a separately
authorized rc.2 build, first set consistent rc.2 version/channel metadata and use
distinct candidate outputs; freshly bind changed source to the candidate and
repeat directly affected frozen-artifact/owner checks. Existing rc.1 source-binding
records continue to describe rc.1, not these unbuilt changes.

Current gate: **READY TO BUILD WINDOWS 1.0.0-rc.2 CANDIDATE**.
Build performed: **NO**. Final Windows v1 owner acceptance: **PENDING on rc.2**.
