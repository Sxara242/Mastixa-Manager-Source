# Official service verification — Phase 3, 2026-09-09

The [official INSPIRE description](https://www.ktimatologio.gr/pliroforiako-yliko/geoxorika/42)
describes public cadastral diagrams and links to
`https://www.ktimanet.gr/geoportal/catalog/main/home.page`.
A direct HTTPS request to that exact published portal returned **HTTP 404**.
This result concerns only the old portal; it does not establish the status of
the separately published ArcGIS parcel service.
The [official service page](https://www.ktimatologio.gr/e-services/23) describes
INSPIRE access but exposed no verified query service/capabilities.

## Separately requested ArcGIS parcel layer

The user supplied this exact published service for independent verification:
`https://gis.ktimanet.gr/inspire/rest/services/cadastralparcels/CadastralParcel/MapServer/0`.
Direct HTTPS requests were made to the layer HTML endpoint, layer `?f=pjson`,
layer `?f=json`, and parent `MapServer?f=pjson`. All returned **HTTP 404** at the
same requested URL. Responses were `text/html` with title `404- Ktimatologio`,
not ArcGIS REST metadata or an ArcGIS JSON error. Raw reachability evidence is
retained locally in `.tools/cadastre-reachability.json` (no parcel records fetched).

| Required check | Actual result |
| --- | --- |
| Reachability | Host responds; specified resource returns HTTP 404 in this environment |
| REST metadata | Not returned |
| Capabilities / operations | Unverifiable without metadata |
| Actual layer fields | Unverifiable; no field names assumed |
| Queryable KAEK / equivalent identifier | Unverifiable |
| Geometry type | Unverifiable |
| CRS / spatial reference | Unverifiable; EPSG:2100 not assumed |
| Official geometry query | Not tested without verified schema/capability |
| JSON / GeoJSON support | Unverifiable; JSON metadata requests returned HTML 404 |
| Query-by-KAEK feasibility | Pending live metadata verification |

This is **BLOCKED / UNVERIFIABLE FROM THIS ENVIRONMENT ON THIS DATE**, not a
permanent finding that the service lacks query support or no longer exists.
The old portal failure and the independent ArcGIS failure are distinct evidence.
Recheck this published layer when access changes; no private endpoint is substituted.

The layer schema, KAEK attribute, geometry schema, source CRS,
query support and response formats remain **NOT VERIFIED / BLOCKED** in this run.
No browser-internal maps.ktimatologio endpoint is used. No EPSG:2100 assumption is
made for cadastral data. A provider must not be enabled until these capabilities
and its attribution/license are verified. Authorized manual/file imports remain
the fallback. Synthetic tests must never be labeled live cadastral retrieval.

Source attribution for future verified cadastral responses:
«Πηγή δεδομένων: Ν.Π.Δ.Δ. ΕΛΛΗΝΙΚΟ ΚΤΗΜΑΤΟΛΟΓΙΟ».

No provider granting offline tile downloads is configured. Offline pack download
must remain unavailable with an explicit reason; neutral geometry/GPS rendering
does not depend on a basemap. Google/Sentinel are optional provider extensions;
no credentials, imagery scraping, or OSM bulk prefetch are introduced.
