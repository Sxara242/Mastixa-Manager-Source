> Retained historical engineering record, sanitized for public review.
> Current status: [RELEASE_STATUS.md](RELEASE_STATUS.md). This record does not
> establish approval of the current source or a new binary release. Local-only
> receipt paths refer to privately retained evidence, absent from this snapshot.

# Windows v1 Manual QA — Owner Acceptance & Fix Plan

**Date:** 2026-10-03 <br>
**Branch:** `icon-runtime-qa-final` <br>
**Application under test:** Mastixa Manager v0.40.0-alpha.2 <br>
**Scope:** Windows v1 owner/manual QA, 400-step checklist, real-world cross-feature workflow, persistence, backup/restore, profile isolation, year context, reports, exports and window behavior.

## Status

**MANUAL WINDOWS v1 QA: COMPLETE — 400/400 steps reached.**

This is **not** a release-ready verdict. The manual QA completed successfully as a discovery/acceptance pass and produced a concrete v1 fix backlog. Confirmed defects and requested UX changes below must be addressed, regression-tested, rebuilt and owner-retested before the final Deep Cross-Feature Real-World Usage Audit and release gate.

The final manual steps 397–400 completed successfully: final backup succeeded and the application closed normally.

## Important working-tree warning

During this QA cycle, valuable local fixes were made and owner-retested. At the time this report was written they must be treated as potentially **uncommitted/unpushed local work**. Before any Codex batch:

1. run `git status`;
2. inspect `git diff` / `git diff --cached`;
3. preserve all existing local changes;
4. do **not** reset, checkout-over, discard or rewrite the working tree.

Known locally changed areas from the QA cycle include at least:

- `app/money.py`
- `app/sales.py`
- `tests/test_transaction_integrity.py`

## Fixes already implemented and owner-retested during QA

### Money manual INSERT placeholder mismatch

Problem:
- Income INSERT had 8 columns / 7 placeholders.
- Expense INSERT had 9 columns / 8 placeholders.
- Manual entries failed with SQLite placeholder errors.

Fix:
- corrected placeholders in `app/money.py`;
- added focused regression tests in `tests/test_transaction_integrity.py`.

Evidence:
- focused module: **30/30 PASS**;
- rebuilt/installed alpha.2 owner retest: **PASS**.

### Sales product/unit KPI handling

Problem:
- Sales KPI totals mixed products/units.
- Product-specific quantities could be shown as if all were kg.
- Product selection did not fully drive KPI/list state.

Fix:
- product selector positioned above KPIs;
- selected-product KPIs are product-specific;
- exact stored unit is shown;
- "All products" does not pretend incompatible quantities share one unit;
- list/KPIs refresh on product change;
- table prices/quantities/warnings use product unit.

Evidence:
- focused verification: **46/46 PASS**;
- installed alpha.2 owner retest: **PASS**.

These fixes must be preserved through all later batches.

---

# Confirmed v1 blockers / functional defects

## 1. Global active/effective year consistency

**Severity: High / foundational.**

Manual QA proved that the global active working year is not consistently honored across annual forms and views.

Confirmed examples with active year **2027** while real system year was **2026**:

- Inventory initial stock logic used system year.
- Inventory new movement defaulted to 03/10/2026.
- Inventory movement reset/clear returned to 03/10/2026.
- Irrigation & Fertilization / farm activity defaulted to 03/10/2026.
- Equipment maintenance/service defaulted to 03/10/2026.
- Crop Program application/generation defaulted to 2026.
- equivalent year-sensitive call sites require repository-wide audit.

Required fix:
- audit direct `QDate.currentDate()`, `date.today()`, `datetime.now()/today`, `.year()` uses;
- distinguish true wall-clock timestamps from annual business-record defaults;
- annual records must use shared year-context helpers such as `working_context_date()`, `effective_working_year(db)`, `active_working_year(db)`, `qdate_in_year()`;
- form reset/clear must return to effective working year;
- editing an existing record must preserve its stored date unless explicitly changed;
- correction mode must default new records to correction year.

### Inventory initial stock

Confirmed source behavior:
- lock check used `QDate.currentDate().year()`;
- generated initial "Διόρθωση +" movement used system date.

Required:
- lock check and generated movement date must use effective working year/date.

### Annual list views vs active year

Owner expectation confirmed during QA:
- when active year is 2027, annual list views should not behave as if 2026 is the current working dataset;
- Money and Production currently continue showing prior-year rows by default;
- Dashboard then aggregates those prior-year rows into current totals.

Required:
- annual list views should align with active year by default;
- if "All years" access is useful, expose it explicitly as a filter rather than silently mixing years;
- do not delete or hide historical data permanently.

## 2. Temporary correction mode does not reliably bypass physical lock

**Severity: High.**

Reproduced workflow:
- physical lock on 2026;
- active year 2027;
- temporary correction mode for 2026 entered successfully;
- global correction UI/warning appeared correctly;
- attempted Money entry in correction mode;
- record did not persist because page-level Money guard still checked physical lock directly.

Root architectural issue:
- some pages use physical `is_year_locked()` semantics instead of the effective write-lock rule.

Required:
- a correction session makes exactly that one physically locked year writable for the lifetime of the in-memory correction session;
- physical lock row remains locked;
- all other locked years remain blocked;
- restart/crash resets correction state and returns to safe locked behavior;
- audit all annual mutating modules: Money, Production, Sales, Inventory, farm activities, equipment maintenance, plant protection, labor, plantings, cultivation declarations and any other annual records.

Prefer shared `is_year_write_blocked(db, year)` semantics rather than per-page duplicated logic.

## 3. Locked-year read-only UX

Owner-requested v1 behavior:

- allow navigation/viewing of a physically locked year in **read-only mode**;
- global year bar should clearly show something like:
  - `Κλειδωμένο έτος 2026 — Μόνο προβολή`;
- Add/Edit/Delete remain blocked;
- attempted mutation should explain:
  - year is locked;
  - corrections require `Ασφάλεια → Κλείδωμα Έτους → Προσωρινή διόρθωση`;
- correction mode remains visually distinct and more prominent.

Current behavior blocks simple transition to a locked year.

## 4. Permanent unlock reason/audit gap and Year Lock layout

Confirmed:
- permanent `Ξεκλείδωμα έτους` currently requires no reason;
- audit records the unlock but not a user-supplied reason.

Owner-requested layout:
- for a selected locked year, one action area;
- common required field above actions: **Αιτία ενέργειας**;
- side-by-side:
  - **Επεξεργασία κλειδωμένου έτους** → temporary correction;
  - **Μόνιμο ξεκλείδωμα έτους** → permanent unlock;
- both require non-empty reason;
- audit permanent unlock with year, action, reason and timestamp.

## 5. Active-year success confirmation

Owner-requested:
- after a real successful active-year change, show confirmation such as:
  - `Το ενεργό έτος άλλαξε επιτυχώς σε 2027.`
- do not show if selecting same year, failed/cancelled transition, or entering/leaving correction mode.

---

# Cross-feature financial integrity

## 6. Irrigation & Fertilization cost does not sync to Expenses

**Severity: High.**

Reproduced:
- farm activity saved successfully on 03/10/2027;
- linked to `QA FIELD 01 EDIT`;
- cost edited to **5.00 €**;
- activity row correctly showed 5.00 €;
- no corresponding Expense was created/updated.

Source inspection confirms farm activities persist `cost` but do not currently perform the same `sync_expense()` flow used by inventory receipts and equipment maintenance.

Required:
- create activity with cost → create one automatic Expense;
- edit cost → update same linked Expense, never duplicate;
- change relevant date/field/description/partner metadata → keep linked Expense consistent;
- zero/remove cost → defined consistent behavior;
- delete activity → delete linked automatic Expense;
- transaction must be atomic so activity/expense cannot diverge;
- add failure-injection regressions.

## 7. Existing linked-write atomicity must remain intact

Already-fixed linked workflows from prior engineering work must not regress:
- sale ↔ income;
- receipt ↔ expense;
- equipment maintenance ↔ expense;
- inventory consumption links;
- invoice posting paths.

Any new farm-activity expense integration should use the same transaction discipline.

---

# Dashboard / Reports / units

## 8. Dashboard ignores active year

**Severity: High.**

Reproduced with active year 2027:
- Dashboard included 2026 Production, Income and Expenses.
- Example production total showed **175 kg** from:
  - 55 kg (2027 Mastixa)
  - 110 kg (2026 Mastixa)
  - 10 pieces (2026 QA PRODUCT)
  - incorrectly treated as one kg total.

Required:
- Dashboard totals must follow active year;
- prior-year data remains stored but not silently included in active-year KPIs;
- product/unit-aware aggregation required.

## 9. Dashboard mixed-unit aggregation

Confirmed:
- incompatible quantities are summed and labeled kg.

Required:
- never sum kg + pieces + liters/etc.;
- either require a selected product/unit or present separate unit-aware totals;
- "All products" must not fabricate one physical quantity.

## 10. General Reports mixed-unit aggregation

Confirmed in Reports:
- 110 kg Mastixa + 10 pieces QA product displayed as **120 kg**;
- field report showed 120 kg and derived **240 g/tree**, therefore derived KPI was also invalid;
- PDF export inherited the same incorrect totals.

Source areas previously identified:
- `_total_for("production", "quantity_kg", year)`
- `_yearly_rows()`
- `_refresh_fields_table()`
- hard-coded kg/g-tree presentation;
- report snapshot/export paths reuse these totals.

Required:
- product/unit-aware calculations;
- never aggregate incompatible physical quantities;
- field and g/tree calculations only when unit semantics make sense;
- exports must use same corrected canonical calculation layer.

## 11. Annual Report / Sales & Stock unit handling

Manual QA clarified an important semantic point:

**Carry-over stock across years is valid.**

For a selected product, "stock at end of 2027" may correctly include prior-year unsold stock:
- production through 31/12/2027
- minus sales through 31/12/2027.

Do **not** "fix" this by limiting end-of-year stock to only current-year production.

Actual bug:
- "All products" combines incompatible units;
- generic headers/labels say kg even for products stored in pieces.

Example export:
- Mastixa: 65 produced in 2027, 4 sold, carry-over stock 70 — logically valid for that product;
- QA PRODUCT -1: stock 10 pieces;
- UI incorrectly showed combined stock 80 kg;
- CSV headers still said `Παραγωγή kg`, `Πωλημένα kg`, `Μέση τιμή / kg`.

Required:
- per-product rows use actual product unit;
- "All products" must not sum incompatible units into one physical quantity;
- retain correct carry-over semantics per product;
- average price suffix must use actual unit.

---

# Sales source tracking / traceability enhancement

## 12. Sale source: total product stock vs specific field

Current behavior:
- Sales deduct from pooled stock per product;
- user cannot choose which field's production the sale came from.

Owner-requested v1 design:

In **New Sale**, after Product:

**Production source**
- `Total stock of <product>`
- specific field entries, e.g. `QA FIELD 01 EDIT — available X kg`
- other fields with available stock

Behavior:
- choosing a field limits sale to that field's available stock for that product;
- choosing Total Stock preserves current pooled behavior.

Settings:
- **Default sale source**
  - Total stock
  - By field

This setting controls only the default selection; both options remain available in every sale.

Do not require full lot/batch/FIFO implementation for v1 unless explicitly approved later. Product + field is the requested intermediate traceability level.

## 13. Reports: total and per-field sales/stock

Use the same source model as Sales.

Reports should support:
- total product view;
- per-field production;
- per-field sales attributed to that field;
- per-field remaining stock;
- per-field sales revenue;
- total across fields without violating unit semantics.

Suggested filter hierarchy:
- Year
- Product
- Source/Field
  - All fields / total
  - Specific field

Do not duplicate stock arithmetic in Reports; use the same canonical calculation logic as Sales.

---

# UI / UX correctness

## 14. New Expense Cancel button disabled

Reproduced:
- on a new Expense form, after entering `QA CANCEL NEW`, Cancel remained disabled;
- switching tabs preserved draft values;
- opening an existing record and then Cancel works.

Required:
- when a new form becomes dirty, Cancel becomes enabled;
- Cancel clears the unsaved draft and restores default values;
- no record is created;
- existing-record Cancel continues to discard unsaved changes safely.

Consider a reusable dirty-form pattern rather than a one-off fix if several forms have the same behavior.

## 15. Money sort/filter gaps

Manual checklist steps 153–155 were N/A because features are not implemented.

Owner-requested v1 TODO:
- sort by date;
- sort by amount;
- expense filter by category.

## 16. Date display preference

Current Settings has no date display preference.

Owner-requested v1:
- configurable display format;
- default: **dd/MM/yy**;
- options at least:
  - dd/MM/yy
  - dd/MM/yyyy
  - yyyy-MM-dd
- display only: canonical DB storage remains ISO `yyyy-MM-dd`;
- changing preference must not alter actual dates, sorting or export semantics.

## 17. Product unit editable-combo malformed input

Observed:
- editable unit input could produce malformed concatenation such as `2τεμάχια2`.

Required:
- clean custom-unit behavior or controlled non-editable choices;
- if custom units remain supported, validate and save exact intended value without accidental concatenation.

## 18. Dark-theme context menu contrast

Confirmed in coordinate input:
- right-click context menu had very light background with nearly white/disabled-looking text;
- Undo/Copy/Paste/etc. difficult to read.

Required:
- theme-consistent readable context-menu foreground/background/disabled states.

## 19. Crop Program recurrence spinbox controls

Confirmed:
- arrow controls for Base Year / Every N years rendered incorrectly in dark theme;
- arrow buttons were not clickable;
- keyboard typing worked.

Required:
- fix QSpinBox styling/property conflict;
- arrows visible and clickable in light/dark themes;
- preserve recurrence values.

Recurrence logic itself passed manual persistence testing.

## 20. History/Audit page blank

Observed:
- `Αναφορές & Έλεγχος → Έλεγχος & Δεδομένα → Ιστορικό Ενεργειών` displayed a blank content area.

Required:
- verify whether lazy-loading/navigation wiring or page rendering is broken;
- page must show audit data or a clear empty-state, never an unexplained blank page.

## 21. Responsive scrolling / clipping

Confirmed:
- Income page can be cut off in smaller window;
- Expenses page can be cut off;
- Production page can be cut off;
- windowed Expenses text clipping was observed.

Required:
- outer vertical scroll/responsive layout where needed;
- important buttons and fields remain reachable at supported minimum window size;
- do not silently crop forms.

Potential similar behavior in other pages should be included in the UI sweep, but do not claim unconfirmed pages as reproduced defects.

## 22. Window movement/resize performance

Confirmed:
- resize/maximize/restore is not smooth;
- dragging the non-maximized window has visible lag/stutter/delay.

Functionally usable, therefore not a data-integrity blocker, but it is a v1 performance defect.

Required:
- profile redraw/layout/repolish work during move/resize;
- identify expensive repeated refreshes/styles/layout operations;
- optimize without changing data behavior.

## 23. First-load page sluggishness

Observed:
- first navigation to some lazy pages can take roughly 2–3 seconds;
- subsequent cached visits are faster.

Treat as performance polish unless profiling demonstrates a blocking issue.

## 24. Alerts/non-Dashboard metric contrast

Earlier QA observed dark-theme KPI text with poor contrast in Alerts/non-Dashboard metrics. Dashboard metric value contrast later appeared corrected.

Required:
- targeted theme sweep for metric cards outside Dashboard;
- do not re-open the already-correct Dashboard styling unnecessarily.

---

# Export / reporting UX

## 25. Data Quality CSV readability

CSV is technically valid and should remain machine-readable.

Owner feedback:
- raw semicolon-separated output is hard to read visually.

Requested:
- keep clean CSV;
- add human-friendly Excel (.xlsx) export with sensible column widths, headers and wrapping.

## 26. Annual Report export formats

Current annual report export is CSV-only.

Owner-requested v1:
- replace/augment with **Export ▾**
  - PDF
  - Excel (.xlsx)
  - CSV
- PDF should be the most visible human-readable option;
- all formats must use the same corrected unit-aware report model.

---

# Packaging / branding / release polish

## 27. Task Manager application description

Observed in Windows Task Manager:
- process description displayed **"Local farm management application"**.

Owner-requested:
- show clear application branding, preferably **Mastixa Manager**.

Review:
- File Description
- Product Name
- application name
- company/publisher metadata where applicable
- installer/exe properties consistency

## 28. Unsigned installer reputation

Bitdefender may flag locally built unsigned installer as PUA/reputation issue.

Not treated as an application functional bug.

Release work:
- decide signing/reputation strategy;
- keep this separate from runtime QA.

## 29. Updater end-to-end release gate still pending

Updater was not fully verified end-to-end because release feed/version URLs were not yet a real v1 release candidate.

Final release gate must cover:
- real version bump;
- feed metadata;
- URL/SHA verification;
- older build detects update;
- download/verify/launch installer;
- profile/data/backups survive update.

---

# Scope / accepted N/A items

## Invoice Documents / attachments

Current Windows Invoice Documents UI is explicitly **under construction**.

Therefore manual attachment steps were N/A in this build, including the real-world attachment step and final attachment persistence check.

This is not to be reported as a runtime failure for the accepted Windows v1 scope unless the feature is re-enabled before release.

Profile package V2 attachment handling was separately verified at the package level.

## Production vs Inventory supplies

Production stock and Inventory supplies are separate concepts in the current architecture.

Do not "fix" Production rows by forcing them into the supplies Inventory module unless a future design explicitly changes this contract.

## Coordinate export with no geometry

"0 / 1 fields have saved boundaries" when a field has no geometry is expected behavior, not a bug.

## Icons

Earlier icon alignment/artifact suspicion was explicitly rejected by the owner after retest.

**Do not include an icon fix.**

---

# Major workflows that passed manual QA

The following areas passed their intended manual checks, subject to the known issues above:

- Money manual entry after placeholder fix.
- Sales product-specific KPI/unit behavior after focused fix.
- Profile isolation across repeated profile switches.
- Profile V2 export/import.
- DB backup creation and restore.
- Restore removed post-backup data and preserved earlier QA data.
- Coordinate export:
  - WGS84;
  - EPSG:2100 source XY;
  - transformation between source and WGS84;
  - KAEK/field metadata;
  - PDF formatting/Greek text.
- Recurrence:
  - weekly;
  - changed to every 2 weeks;
  - persistence across reopen;
  - generated dates 01/05, 15/05, 29/05 for the shortened test window;
  - no duplicate generated tasks observed.
- Persistent field links survived restart, backup/restore and profile import/export.
- Invalid numeric input:
  - letters rejected safely;
  - negative amount not accepted;
  - required Description validation prevents partial save.
- Double-save protection:
  - Expense created once;
  - Production created once.
- Repeated profile activation with full client refresh:
  - no crash/freeze;
  - no accidental duplicate profiles;
  - no cross-profile field/Money leakage.
- Rapid year switching:
  - switching itself stable;
  - year-dependent content defects are separately listed.
- UI stress navigation:
  - no crash/freeze;
  - no duplicated dialogs/widgets;
  - profile/year context did not spontaneously change.
- Window lifecycle:
  - X close/reopen;
  - Alt+F4/reopen;
  - Task Manager termination/reopen;
  - DB/profile/field/Money survived.
- Delete confirmation behavior:
  - Expense cancel-delete preserves row;
  - confirmed delete removes row and survives restart;
  - Field delete cancel preserves;
  - confirmed field delete removes and survives restart.
- Localization sweep across main pages passed with no obvious untranslated/broken text.
- Real-world flow:
  - Inventory receipt 5 units × 4 €;
  - automatic Expense 20 € created;
  - farm activity linked to field;
  - Production +10 kg created;
  - Sale 4 kg × 10 €/kg created;
  - automatic Income 40 € created;
  - restart persisted Money, Production and Inventory data.
- Final manual backup succeeded.
- Final normal close succeeded.

---

# Selected manual QA step outcomes

This is a summary, not a replacement for the original 400-step checklist.

- 1–183: completed before this final continuation; known findings folded into this report.
- 184–185 Reports financial KPIs: PASS.
- 186–190 Reports production/unit/field calculations: FAIL due mixed-unit aggregation.
- 191 Reports year filter: PASS.
- 192 profile isolation: PASS.
- 193–198 Data Quality CSV: functional PASS; readability TODO; date/decimal-specific checks N/A where data absent.
- 201–208 coordinate export: PASS; dark context-menu contrast defect found.
- 209–213 profile package V2 export: PASS.
- 214–225 DB backup/restore: PASS.
- 226–228 attachments: N/A.
- 229–236 profile V2 import: PASS; attachments N/A.
- 237–246 recurrence: PASS; spinbox arrow UI defect found.
- 247–252 persistent field link: PASS based on stronger restart/restore/profile evidence.
- 253–254 temporary correction entry/UI: PASS.
- 255 temporary correction write: FAIL in Money due physical-lock guard.
- 256–257 leaving correction mode: PASS.
- 258 dependent on failed write: FAIL/blocked.
- 259–260 correction persistence check: N/A until write fix.
- 261–270 date-display preference: N/A in current build; v1 TODO created.
- 271–274 new Expense Cancel: FAIL because Cancel disabled.
- 275–279 existing Expense Cancel: PASS.
- 280–286 invalid input/validation: PASS.
- 287 Cancel: blocked by known new-form Cancel defect.
- 288–292 double-save protection: PASS.
- 293–300 profile switching/isolation: PASS.
- 301 rapid year switching itself: PASS.
- 302–305 active-year content/Dashboard consistency: FAIL due year-context aggregation/view behavior.
- 306–310 UI stress navigation: PASS.
- 311–317 window behavior: functionally PASS; performance defect recorded.
- 318–323 normal close and Alt+F4 recovery: PASS.
- 324–330 Task Manager termination/recovery: PASS; metadata branding TODO found.
- 331–350 delete behavior Expense/Field: PASS.
- 351–361 localization sweep: PASS.
- 362–384 real-world workflow/persistence: functional core PASS with known year-context, unit and farm-activity expense-sync defects.
- 385–396 final persistence: PASS for retained data; attachments N/A; known Dashboard/Reports defects remain.
- 397–400 final backup/close: PASS.

---

# Prioritized Codex fix batches

The owner wants fixes delivered in meaningful batches, not tiny one-off prompts. Each batch should include source audit, root-cause reasoning, implementation, focused regressions and a report before moving to the next batch.

## Batch 1 — Year Context & Year Lock Core

**Complexity: High.** <br>
**Reasoning:** Foundational shared behavior. Fixing pages independently would duplicate logic and cause repeated regressions.

Scope:
- repository-wide year-sensitive default audit;
- active/effective year for new/reset forms;
- Inventory initial stock year handling;
- temporary correction effective write-lock semantics;
- locked-year read-only navigation;
- year-change success confirmation;
- Year Lock action layout;
- required reasons and permanent-unlock audit;
- focused regression suite across shared helpers and representative workflows.

Do not mix Dashboard/Reports aggregation, sales field sourcing, activity-expense sync or performance into this batch.

## Batch 2 — Cross-feature financial synchronization

**Complexity: High.** <br>
**Reasoning:** Data integrity across linked tables must be atomic before report calculations are trusted.

Scope:
- Irrigation/Fertilization cost ↔ Expense;
- create/update/delete/zero-cost semantics;
- atomic transaction and rollback tests;
- reverify existing sale-income, receipt-expense, maintenance-expense contracts;
- preserve profile/year locks and correction semantics from Batch 1.

## Batch 3 — Dashboard, Reports and unit-safe aggregation

**Complexity: High.** <br>
**Reasoning:** Multiple pages currently calculate similar totals differently. Fix canonical aggregation before cosmetic report work.

Scope:
- Dashboard active-year filtering;
- Dashboard incompatible-unit handling;
- general Reports production/year/field/g-tree unit safety;
- Annual Report actual-unit labels;
- preserve valid carry-over stock per product;
- exports consume the same corrected calculation layer;
- regression fixtures with kg + pieces in multiple years.

## Batch 4 — Sales source tracking and per-field reporting

**Complexity: Medium–High.** <br>
**Reasoning:** New data relationship/schema behavior; should follow stable unit/stock calculations from Batch 3.

Scope:
- Sale source = Total product stock or Specific field;
- per-field available stock invariant;
- Settings default source preference;
- migration/backward compatibility;
- Reports total + per field;
- no full lot/FIFO system unless separately approved.

## Batch 5 — UI/UX correctness

**Complexity: Medium.**

Scope:
- new Expense dirty-form Cancel;
- Money sort/filter;
- date display preference default dd/MM/yy;
- product-unit input validation;
- dark context-menu contrast;
- recurrence spinbox arrow controls;
- blank Audit History page;
- responsive scrolling/clipping;
- remaining metric-card contrast sweep.

## Batch 6 — Window/UI performance

**Complexity: Medium.**

Scope:
- profile resize/move lag;
- identify repaint/repolish/layout hot paths;
- first-load lazy page latency;
- optimize without altering business logic;
- measure before/after where practical.

## Batch 7 — Export, branding and release polish

**Complexity: Medium–Low.**

Scope:
- Data Quality XLSX human-readable export;
- Annual Report PDF + XLSX + CSV export menu;
- Task Manager/file metadata branding;
- version string cleanup;
- installer signing/reputation plan as release concern;
- updater end-to-end preparation.

## Batch 8 — Regression consolidation + rebuilt owner retest

After fixes:
- run focused new regressions;
- run broader Desktop suite;
- rebuild installer;
- targeted owner retest only for changed/affected areas;
- do not mechanically repeat all 400 steps unless a broad regression justifies it.

## Batch 9 — Deep Cross-Feature Real-World Usage Audit

Mandatory final engineering audit before release:
- compound workflows, not isolated button tests;
- roughly 60–100+ realistic scenarios as needed;
- include PASS baselines and every fixed defect;
- examples:
  - Production → Sale → Income → edit → restart → year switch → backup/restore;
  - Receipt → Expense → edit/delete → restore;
  - locked year → correction → linked writes → finish → restart;
  - profile switch → year switch → reports/export;
- GUI-only visual behaviors remain manual verification.

## Batch 10 — Final Windows v1 release gate

Only after the deep audit:
- version bump;
- updater feed/URL/SHA;
- clean package/install/update;
- data/profile/backups survive;
- final security/privacy/licensing/distribution checks;
- final factual release report.

---

# Release verdict at this checkpoint

**Manual QA is complete. Windows v1 is not yet release-ready.**

The application demonstrated strong persistence, backup/restore, profile isolation, coordinate export, recurrence, validation, delete behavior and core real-world linked workflows. The remaining blockers are concentrated in shared year-context semantics, correction-mode write guards, cross-feature financial synchronization and unit-safe reporting. These should be fixed in the prioritized batches above, followed by regression testing, rebuilt owner retest, the Deep Cross-Feature Real-World Usage Audit and the final release gate.
