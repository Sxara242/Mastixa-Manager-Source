# Phase 14E — Aggregate replanting history

Phase 14E separates planting positions from the number of plants that have historically passed through those positions.

## Semantics

For a planting batch:

- `trees_planted` keeps its existing meaning and is the number of original planted positions.
- `trees_alive` remains the current number of living trees and may never exceed the original positions.
- A replacement/replanting is an append-only `planting_replantings` event with date, positive tree count and notes.
- `replantings` is the sum of all replanting events.
- `historical_plantings = trees_planted + replantings`.
- `historical_losses = historical_plantings - trees_alive`.
- `vacant_positions = trees_planted - trees_alive`.

Example: 500 original positions, 28 losses, then 28 successful replacements gives 500 living positions, 28 replantings, 528 historical plantings, 28 historical losses and 0 vacant positions.

This deliberately does **not** rewrite the original 500 to 528. The field still contains 500 planting positions; 528 describes how many plants have been planted over time.

## Persistence

Windows stores append-only events in `planting_replantings` with a foreign key to `planting_batches`. Windows full-SQLite backups therefore include the history automatically.

Android uses the same business semantics and an additive `planting_replantings` table. The Android logical backup schema is version 17; schema 16 and older backups remain accepted and restore with an empty replanting history.

Replanting events cannot predate the original planting date. Event identifiers are immutable: corrections are represented by later history work rather than silently rewriting an existing event.

## Scope

Phase 14E is the shared data/history layer. It does not force users who only need aggregate planting counts to register individual trees. Individual tree tracking from Phase 14A–D remains optional and independent from these aggregate replacement totals.
