> Retained historical engineering record, sanitized for public review.
> Current status: [RELEASE_STATUS.md](RELEASE_STATUS.md). This record does not
> establish approval of the current source or a new binary release. Local-only
> receipt paths refer to privately retained evidence, absent from this snapshot.

# Windows 1.0.0-rc.2 — owner checklist, pending artifact validation

RELEASE-INFRA / DESKTOP. Candidate is NOT BUILT. All checks are pending. The owner
executes this checklist only after actual rc.2 artifact validation passes and exact
installer/installed EXE hashes are supplied. No agent result grants owner acceptance.
Use an isolated installation and synthetic or backed-up QA data. Keep production intact.

## A. Preserved rc.1 acceptance behavior

- [ ] Exact installed rc.2 identity/hash pair, channel rc, unsigned state understood;
      official x64 VC Redist >=14.51.36247.0; AGPL/source/legal access.
- [ ] Startup/basic navigation and input; saved records; light/dark/language persistence.
- [ ] Production save, Product sale stock/arithmetic, Expenses save and report totals.
- [ ] Backup, restore, automatic pre-restore safety backup, profile export and recovery.
- [ ] Annual calculations/PDF layout; GIS EPSG:2100/polygon persistence.
- [ ] Local staging updater shows rc.2/rc; no production download or installation.
- [ ] Shutdown/restart; repair; uninstall KEEP DATA/reinstall preserves QA data.

## B. Fix Batch #1 changes

- [ ] FIX 1: Warehouse shows produced products separately from supplies; 120 kg minus
      101 kg sold gives 19 kg; physical stock carries across year changes.
- [ ] FIX 2–3: Dated pages/KPIs follow effective year; empty managed years selectable;
      master data stays visible; physical availability remains all-time.
- [ ] FIX 4–5: ±1/manual transitions validate/confirm; cancellation preserves draft;
      Year Lock defaults to normal active year and confirms actual selected year.
- [ ] FIX 6: Locked-year create/edit/delete blocked across dated modules and cross-year
      moves; no partial write or indirect expense/inventory bypass.
- [ ] FIX 7: Correction with reason permits intended CRUD before Sales first opens;
      cached pages refresh; other years/profiles denied; reasons persist; restart exits.
- [ ] FIX 8: Exit correction stays on locked correction year read-only; separate return
      restores normal active year; banners and cancellation remain correct.
- [ ] FIX 9: First typing 12; comma/dot decimals; paste/replacement/delete; units,
      precision/bounds/empty-as-zero behavior work in the affected forms.
- [ ] FIX 10–11: Annual entry selects effective year, manual choice stays on-page;
      each product's weighted revenue/sold average uses its own unit; no-sales dash;
      mixed-unit overall average dash; CSV/XLSX/PDF totals and layout correct.

Invoices remain outside Windows v1 scope; PDF primitive artifact validation is
required. Cosmetic findings: UI/POLISH FOLLOW-UP. Record blocking usability or
data-integrity failures with exact steps and expected/actual behavior.

Owner result: date/environment/installed path; verified hashes; A/B results; blockers;
informational items; explicit ACCEPT or REJECT. Decision remains PENDING.
Issue #1 stays OPEN until candidate artifact validation, owner acceptance and source
push have all passed, followed by separately authorized closure/publication steps.
