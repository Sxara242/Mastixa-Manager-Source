# Phase 9C — Cultivation source extension: PASS

Base checkpoint: `2454a7df5391d924e719e9c2e47bf6625787e60a`.
Scope follows `PHASE9A_ACTIVITY_CONTRACT.md` and the six-source Windows
projection specified in `PHASE9B_SCHEMA_COMPATIBILITY.md`.

This package adds the three remaining date-only cultivation sources together:

| Table | Source reference type | Kind | Date |
|---|---|---|---|
| planting_batches | planting_batch | planting | planting_date |
| plant_protection_records | plant_protection | plant_protection | application_date |
| labor_entries | labor_entry | cultivation_work | work_date |

All use their existing local PK and field_id. No business data is copied.
The seven required contract fields, normalization, ordering and scope ownership
remain unchanged. No optional display/status values are invented. Missing module
tables are skipped. Planting/protection retain their actual NOT NULL field links;
labor supports NULL unlinking. Source records remain authoritative.

Implementation only extends the fixed source list and its kind mapping; the
savepoint, caller connection, read-only queries and sorting are unchanged.
No schema/migration, UI, Android or sync changes.

Verification: `python -m unittest tests.test_activity_projection -v`:
**26/26 PASS (0.730s)**, including the unchanged previous 18 tests and 8 new tests.
New coverage: exact projection/field filtering for every added source;
update/field move without duplicate identity; deletion and applicable unlinking;
separate profile connections; absent optional columns/tables and nullable
synthetic values; existing date rules; mixed ordering and distinct same-day
records; controlled failure on a newly added source with pending caller changes.
New read probes enforce query_only and check logical dump, total_changes and
transaction state. Existing 9C4 snapshot and transaction tests also pass.

Fixtures use source-derived DDL with foreign keys enabled. Deliberately minimal
nullable slices test defensive reads without changing real source constraints.
No full Desktop or Android suite/build was run for this package.

Next remaining 9C source: GIS observations (`geo_points` via `parcel_geometry`),
with recorded epoch timestamps, active parent filtering and instant ordering as
defined in 9A. This is not implemented here. Windows UI belongs to 9D, Android UI
to 9E and common sync reference mapping to 9F. This package does not complete
all of Phase 9. No commit or push was performed.
