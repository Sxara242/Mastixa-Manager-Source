# Phase 3 implementation and verification

Both clients preserve original geometry/CRS, normalized WGS84, ordered parts/rings,
geodesic area/perimeter, centroid, bbox, source and update metadata. Geometry is
validated before transactional replacement with an expected revision. No geometry
repair silently changes imported boundaries. Local parcel scope is at most five
degrees, below 85° latitude, and 20,000 vertices.

Desktop imports GeoJSON, KML, 2D GML, a single polygon Shapefile ZIP and straight
closed 2D DXF polylines. Android imports GeoJSON, KML, supported 2D GML and manual
XY coordinates. Android Shapefile/DXF requires conversion on Desktop. Unsupported
CRS/axis configurations fail explicitly instead of guessing. Both maps have pan,
zoom, fit, boundaries, centroid, vertices, source metadata and optional OSM.

Android ParcelMapActivity uses device GNSS in the foreground only (5 seconds /
2 metres). It requests precise-location permission after a user action, displays
fix time/accuracy/bearing/speed where available, identifies containing local
parcels, and distinguishes fixes older than 30 seconds. Containment describes the
fix center and does not imply the accuracy circle is wholly inside the parcel.
No background location permission/service is used. Callbacks stop on pause;
permission denial leaves local maps available. Viewport/toggles/provider and
import CRS are retained across activity state restoration.

Eight point categories support local creation/edit/delete. Android can capture
the current fix; Desktop supports declared coordinates and accuracy. Tracks
start/pause/resume/stop on Android, persist each accepted fix, and keep segment
breaks across pauses so distance excludes unobserved movement. Interrupted
recording reopens paused without inventing elapsed time. Desktop stores and
displays the same ordered track/segment concept. Sync transport is phase 6.

OSM requests only visible tiles after explicit selection. Both clients use a
bounded HTTP disk cache respecting server expiry and identify Mastixa in the
User-Agent. Attribution remains visible. No bulk download or offline pack
provider is fabricated. The default neutral background, geometry, points and
GPS require no network. Android responds to network changes. Optional Google
satellite and Copernicus services remain unavailable until official licensed
provider configuration is supplied.

Live Cadastre retrieval is externally blocked as described in
GIS_PROVIDER_VERIFICATION.md: the specific ArcGIS layer and metadata returned
HTTP 404, independently of the old INSPIRE portal. Actual fields/CRS/query
capability remain unknown; no permanent service-unavailable claim is made.

## Evidence

- Mandatory schema-fixture audit and requested full rerun: 105 passed, 90.226s;
  see SCHEMA_13_TEST_AUDIT.md.
- New Android track/UI/storage checks: 8 passed, 7.961s.
- Desktop new object/overlay checks: 2 passed, 0.431s.
- Android build `assembleDebug assembleChecks assembleChecksAndroidTest lintDebug`:
  passed, 17s; lint 0 errors / 8 existing warnings.
- Desktop live OSM: `.venv/Scripts/python.exe -X utf8 .tools/verify_live_desktop_map.py`:
  24 tiles decoded, zero failed/pending; synthetic temporary database only.
- Android live OSM UI selection/decoding and completed lifecycle pause:
  `am instrument -w -e live_osm true -e class gr.mastixa.manager.ParcelMapUiTest#offlineMapFixPointTrackAndBackgroundPause gr.mastixa.manager.checks.test/androidx.test.runner.AndroidJUnitRunner`:
  passed, 6.034s, `/sdcard/mastixa-live-osm-final-tests.txt`.
- Screenshots inspected: `.tools/parcel-map-osm-desktop.png`,
  `.tools/parcel-map-android.png`, `.tools/parcel-map-osm-android.png`.
- Full post-phase Android: **111 passed, 102.731s**, log `/sdcard/mastixa-phase3-full-tests.txt`.
- Full post-phase Desktop: **34 passed, 174.833s**, command `.venv/Scripts/python.exe -X utf8 -m unittest discover -s tests -v`, log `.tools/phase3-desktop-tests.txt`.

Full lifecycle/process recreation, native GNSS delivery, airplane-mode and broad
regression cases continue in phase 8. Physical-device antenna accuracy, battery
and field reception need real-device testing. No such field test is claimed.
