# Phase 12D — Crop Program Windows UI

Phase 12D exposes the Phase 12 crop-program model in the Windows client without changing the persistence contract.

## Scope

- Create, edit and archive crop-program templates.
- Add, edit and remove fixed-date or interval-window rules.
- Assign an active program to a field and season year.
- Generate or regenerate deterministic planned tasks through `CropProgramStore`.
- View generated tasks and mark them pending, completed or skipped.
- Keep archived templates read-only; archiving removes pending tasks but preserves decided history according to the Phase 12B contract.
- Keep existing main-window page indices stable by appending the page at startup.

No agronomic schedules are pre-seeded. Users define or approve their own rules.

## Localization and dates

The page has Greek source text plus an English language pack extension. Month/day rule inputs deliberately use numeric `dd/MM` controls rather than locale month-name dropdowns. This prevents the new UI from showing English month names while the application is in Greek and is covered by a regression test.

The previously reported month-name issue in other filters remains a separate localization audit item until its original control is identified.

## Quality gate

Desktop tests cover the new read API, program save/list/detail behavior, archive filtering, UI persistence, generated-task rendering, startup navigation integration, English translations and numeric rule-date display.
