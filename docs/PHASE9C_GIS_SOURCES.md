# Phase 9C GIS observations — PASS

- Mapping from 9A: `geo_points` with `point_type IN ('note','problem')`
  projects as `source_ref.type=geo_point`, `kind=observation`. Tracks and other
  point types are not observation sources.
- Association: join point.parcel_id to parcel_geometry.id, then parcel.field_id
  to an existing fields.id in the caller's authorized profile connection.
  Point and parcel must have deleted_at IS NULL (zero is a tombstone too).
  Wrong-field, NULL/unlinked and dangling associations are excluded. Missing
  GIS tables are skipped without creating them.
- Time: integer `created_at` UTC epoch milliseconds is preserved as event_at;
  event_date is its UTC calendar date, time_basis=recorded. Zero and negative
  epochs are valid within Python's calendar range. No local-time conversion,
  updated_at substitution or current-time fallback. NULL, non-integer storage
  values and out-of-range timestamps yield null event_date, unknown time_basis
  and absent event_at. SQLite INTEGER affinity applies before values are read.
- Ordering: date descending; within a date, timestamped entries first ordered
  by event_at descending, then date-only entries; ties use lexical source type
  and ID. Unknown dates last. Existing date-only ordering is unchanged.
- Identity remains (scope_id, source type, source ID, field ID). No event table,
  cache or copied geometry/business data. Updates re-read the same source;
  deletion, tombstoning or unlinking removes the projected item. No cross-device
  identity inference or sync_ref is added; shared mapping remains in 9F.
- Verification: `python -m unittest tests.test_activity_projection -v` ran once:
  **34/34 PASS, 1.232s**. The previous 26 tests remain unchanged and PASS.
  Eight new tests cover normal mapping/type filtering, parent/tombstone rules,
  defensive NULL/dangling associations, invalid timestamps, epoch/UTC boundaries,
  update/move/delete identity, profile isolation, mixed ordering and caller-owned
  transaction preservation on a controlled GIS query failure. Read probes use
  query_only and check logical dump, total_changes and transaction state.
  Source-derived fixtures retain real constraints; a separate damaged-schema
  synthetic slice exercises NULL/dangling cases without altering production DDL.
- Schema impact: none. Transaction implementation unchanged; GIS reads occur
  inside the existing snapshot savepoint. No Android or UI changes. No full
  local suite/build was run. All six initial 9A source types now have Windows
  projection coverage; 9D Windows field-card integration remains next, with
  Android timeline and sync-reference work reserved for 9E/9F.
