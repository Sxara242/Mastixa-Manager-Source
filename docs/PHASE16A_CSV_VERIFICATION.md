# Phase 16A — Windows portable CSV verification

## Resume reconciliation (2026-09-12)

The local checkout was clean at `3e6696d`. Fetch found newer completed work;
it was fast-forwarded to `87bdae11a678542a1cd83343b4899768a5e96cb9`.
No older work was restarted or overwritten.

The handoff's pending Phase 15B CI #104 failed, then the existing
`443eb5f` sensor profile-isolation test fix passed CI #105. Runtime #24 passed.
Subsequent sensor backup, ingestion and view checkpoints already exist.
Latest baseline CI #110 (`34691569937`) and Android runtime #27
(`34691569986`) both succeeded at `87bdae1`.

Repository Phase 15 labels differ from the high-level roadmap: device identity,
units/timestamps and extensible metric semantics are in 15A/B; backup in 15C;
the normalized API/import boundary and retry validation in 15D; view in 15E.
These existing implementations and tests supersede the stale handoff pointer.
Live provider authentication/network integration remains untested and optional;
no credentials or vendor API were introduced.

## Windows gate: PASS

`python -m unittest tests.test_phase16a_csv -v`: **4/4 PASS, 0.006s**.
No Qt page/window was constructed. Tests invoke existing production CSV/table
export methods against synthetic SQLite fixtures with read-only guards.

Verified:
- UTF-8 BOM, Greek text, semicolon/double-quote quoting and embedded CRLF;
- leading-zero string IDs, explicit units, date and UTC timestamp text;
- negative decimal text without locale conversion or precision loss;
- source table export/product filtering and unchanged database contents;
- portable products credential-column exclusion using a synthetic sentinel;
- existing intentional exclusion of legacy farm activity quantity/unit columns,
  while dose/dose_unit remain available;
- empty/missing optional tables without schema creation.

No application, schema, Android or export-format changes. No full suite/build,
emulator restart or rerun of previously green sensor tests.

## Limits and next gate

CSV parsing here proves lexical serialization fidelity, not an application
database import round-trip. NULL and empty text both serialize as empty cells
under the existing format; CSV alone cannot reconstruct that distinction.
The exporter is not an input validator and does not infer dates or units.

Portable export currently exposes the sections in `EXPORT_SECTIONS`: producer,
fields/products, production, activities, labor, plantings, sales, protection,
inventory, equipment, partners, invoice documents, money and declarations.
Later task/plant/sensor tables are not automatically included merely because
they exist; their tested backup formats are separate from this CSV interface.

## Android gate: PASS (2026-09-12)

CI #111 (`34692425915`) completed successfully: Desktop and Android PASS before
this gate started. Windows tests were not rerun.

Focused `connectedChecksAndroidTest` on the existing Medium_Phone emulator,
isolated `.checks` application: **9/9 PASS, 0 failures/errors/skips**.
Only these selections ran:
- `Phase16CsvImportTest`: 4 new tests for Greek/Unicode, BOM, quote/newline
  handling, extra columns, missing/duplicate columns, wrong row lengths/counts,
  invalid UTF-8, malformed quoting, finite dot-decimal numbers, valid leap dates,
  invalid dates/timestamp-in-date rejection, duplicate source IDs and preservation
  of distinct same-day rows.
- `WindowsImportTest`: 3 existing tests for real field import, duplicate/conflict
  handling, recovery backup, invalid input and injected second-insert failure
  rolling back the entire batch and pending queue.
- `ProductionTest#actualWindowsZipRelationshipsRepeatAndBackup` and
  `ProductionTest#failedSaleRollsBackEverythingAndMissingIncomeIsRejected`:
  real Windows fixture ZIP import, relationships, repeat idempotency, backup and
  rollback of related registries/queue on an injected sale failure.

No application code or schema changed. Dates in production CSV are date-only;
UTC timestamp strings are rejected there rather than truncated. CSV metadata
timestamps are not substituted for business dates. Field CSV has no event-date
column. Extra named columns are tolerated by the existing generic row reader;
required/duplicate columns and row lengths are validated. Unknown newer sensor
tables do not become supported imports automatically.

Android CSV export is the existing coordinate export (UTF-8 BOM, semicolon,
quoted/doubled-quote cells, CRLF, numeric coordinate handling). Its implementation
was inspected and the already PASS GIS/export coverage retained without rerun;
there is no generic Android business CSV exporter or Windows CSV importer to
claim as a bidirectional round-trip. Existing normalized backups remain separate.

Functional 16A acceptance is satisfied for the existing supported CSV paths.
The new tests/docs checkpoint's CI must be checked before starting 16B; it is
not claimed green based only on baseline #111. No 16B work started here.
