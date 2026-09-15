# Full QA checklist — phases 8–15

Baseline maps checkpoint: `404bd128d73becb10a64a9efc7c7a148b5eb6ccb`,
tag `maps-before-full-qa`. Both refs pushed normally to
`https://github.com/Sxara242/Mastixa-Manager.git`. Independent bare fetch verified
tree `87de0358c4c10be53c4566bf42739d8af25a5b4a`: 264 files, 114 Android,
identical to the audited local tree. No forbidden-file/credential-pattern findings.

This checklist is based on the actual modules and tests, not a blanket claim
that every edge case has already passed. **Phase 8 is COMPLETE for configured
local/emulator QA**, under the user's final scoped gate: build/compile PASS,
lint 0 errors / 12 warnings, affected lifecycle/permission regressions 2/2 PASS.
Retained and final evidence is in PHASE8_NETWORK_QA.md. Full-suite baselines
were not rerun and must not be described as new final full-suite results.
Phases 9–15 in this checklist remain pending; no new checkpoint was created.

| Area | Existing evidence | Additional audit / explicit limits |
|---|---|---|
| Windows startup/shutdown/profile/language/session | runtime_paths, profiles, profile_switch_ui, language_and_logging, stabilization tests; packaged GIS build and startup/shutdown PASS | Packaged smoke used isolated synthetic data, exit 0 |
| Windows Dashboard/producer/fields/products/partners | all-page refresh, registry CRUD/navigation tests | Review current validation, page lifetime and queries |
| Windows production/sales/income/expense/stock | transaction/idempotence/report tests | Review linked writes, rollback, indexes |
| Windows activities/protection/labor/plantings/equipment/invoices | stabilization and Android export tests | Review legacy compatibility and old-data handling |
| Windows reports/annual reports/field cards/backup/declaration/settings/calendar/search | all-page construction/refresh, report navigation, profile backup tests | Differentiate smoke checks from full interactive coverage |
| Android welcome/profile/language/back/session timer | ProfileFlow, ProfileStore, SessionPolicy, SessionNavigationUi; actual process-loss/reopen and Activity recreation PASS | No claim of physical-device GNSS accuracy |
| Android Dashboard/alerts/catalog/partners | Dashboard, DashboardUi, Catalog, CatalogUi, Partner, PartnerUi | Prior feature checks retained |
| Android inventory/money/production/work/equipment/documents/locks/reports | store + UI suites, ReportsLocks, DocumentsReportsUi | All old migration/backup assertions retained |
| Local databases/migrations/backup | full 48 Desktop / 123 Android baseline; schema 12→13→14, actual 13 backup restore; injected SQLite rollback and orphan prevention PASS | Unmapped GPS records remain pending locally until transferable parcel geometry exists |
| Geometry Polygon/MultiPolygon/holes/order/validity/metrics/containment | test_gis, ParcelGeometryTest, GeoStoreTest | Add discovered boundary cases only; no arbitrary tolerance relaxation |
| CRS/source preservation/axis order/precision | shared published reference fixtures + real cross-runtime EPSG:2100 exchange | Unsupported 3D/CRS rejected; Cadastre layer CRS unknown |
| Coordinate CSV/XLSX/PDF/GeoJSON/KML | programmatic contents + rendered PDF review; queued saves, profile ownership, cancellation, unavailable destination/picker PASS | Arbitrary third-party document providers can leave an incomplete destination on interrupted writes; UI reports this limitation |
| Map/GPS/offline/accuracy/follow/tracks | ParcelMapUi, GpsTrack, GpsFix, live OSM; actual offline/cache/network and GPS service recovery; recreation and process loss PASS | GPS coordinates in callback assertions are synthetic; physical GNSS accuracy/power remains unverified |
| Offline map packs | Accurate blocked state; no illegal prefetch | BLOCKED BY MISSING EXTERNAL SERVICE/CREDENTIALS: licensed provider |
| KAEK provider | Published ArcGIS layer independently returned HTTP404; local import retained | Missing live schema prevents realistic query-field/CRS cases; test provider error contract without pretending official responses |
| Sync A–M master cases | SQLite mocks, lost ACK/retries, offline edits, deletion/geometry conflicts, actual bidirectional runtime exchange | Live Supabase BLOCKED BY MISSING EXTERNAL SERVICE/CREDENTIALS |
| Physical GNSS accuracy/power/field conditions | Emulator logic and mock fixes only | NEEDS REAL DEVICE TEST |
| Performance | Profile-local SQLite, viewport-only OSM, foreground GPS, worker exports | Phase 9: identify measured or obvious N+1/parsing/network/lifetime costs |
| Architecture/error handling/security/static tools | Existing transaction tests, secret scan, Android lint | Phases 10–13 systematic review remains pending |

## Findings queue

- FIXED AND RETESTED: Desktop failed OSM tile recovery and stale aborted reply
  interference. Three targeted tests passed (0.957s), including real local HTTP
  503/recovery, malformed/oversize tile responses, and preservation of geometry.
- FIXED AND RETESTED: Android active track was saved but not drawn until manually
  selected. Seven map/GPS/lifecycle tests passed (10.027s), including recreation,
  preserved viewport, paused recording and no resurrection of stale GPS fixes.
- FIXED AND RETESTED: Android uncached tiles remained blank after reconnect.
  Real network cycle 1/1 passed (9.328s); related regression 5/5 (10.842s).
  Actual disk-cache hits verified offline; same map recovered without restart.
- Candidate: sync document lookup reserializes every record for a single UUID,
  repeated during acknowledgement/apply. Measure and address in phase 9.
- Deferred code-review candidate for phases 9–13, not a reproduced QA failure:
  Android export field metadata is read just before, rather than inside, the
  geometry snapshot transaction. Review consistent snapshot boundary.
- Candidate: source-checkout `run.bat` only installs dependencies for a new venv;
  existing development environments must update requirements (README now explicit).
- FIXED AND RETESTED: Android disabled-GPS status and provider listener recovery;
  actual service transition and stale/duplicate/profile callback protection
  passed 1/1 (24.610s). Final lifecycle/permission regression selection passed 2/2.
- FIXED AND RETESTED: export profile ownership and queued-save cancellation;
  missing-picker error handling; orphan GPS sync records remain pending until
  a transferable parent exists. See final report for exact retained test logs.

Final statuses will use the master specification's explicit tested/failed/fixed/
not-testable/real-device/external-blocked categories. Later phases remain pending
until their corresponding checks and any required fixes are complete.
