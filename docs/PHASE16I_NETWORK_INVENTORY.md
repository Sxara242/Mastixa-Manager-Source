# Phase 16I — network call inventory

Reviewed 2026-09-13. Scope is application paths, with build/OS/external-provider
boundaries distinguished. No packet-capture claim. Core use works without network.

| Platform / path | Destination / outgoing data | Trigger, optionality, background/retry, logging |
|---|---|---|
| Windows `gis/map_view.py`, `providers.py` | HTTPS tile.openstreetmap.org; IP, viewport-derived z/x/y and fixed User-Agent; no parcel name/KAEK or DB upload | Explicit OSM selection; optional; async visible-tile requests and bounded retries while map active; HTTP disk cache. No request/response body logging. |
| Android `AndroidBasemap`, `MapProviders`, `ParcelMapActivity` | Same OSM HTTPS tile endpoint, IP/z/x/y/fixed User-Agent | User-selected OSM, including restored selection; worker requests/cache/retry, close cancels callbacks; no background tracking service or telemetry. Provider receives viewed area, disclosed in UI. |
| Windows pyproj/PROJ | Potential remote grid download determined by PROJ network configuration | Previously environment `PROJ_NETWORK=ON` could enable access without app consent. Now transformer creation explicitly disables PROJ network. Test verifies both context and transformer flags with environment ON. No live grid request made during test. |
| Windows file/backup/export paths | User-selected path may be UNC/network share or synced directory | User controls destination; filesystem/OS may transfer contents. Core works locally. No application automatic cloud upload. Auto backups use the user's configured backup directory and can therefore target a share. |
| Android SAF open/create document | User-chosen local or cloud DocumentsProvider | User initiates import/export; provider may download/upload selected full content, under its own account/policy. No silent provider selection, no broad storage permission. Cancellation/error paths retained; arbitrary provider retry behavior outside app control. |
| Windows external opener | `QDesktopServices` opens backup/log folders or local invoice attachments; OSM attribution link can open browser | User click. OS/default viewer/browser may access a share or perform its own network activity. Not app telemetry; external viewer security is separate. |
| Cadastre / Google / Copernicus / offline packs | Documented providers, currently unavailable placeholders | No active fetch: Cadastre provider raises explicit unavailable error; missing services are not fabricated. Future integration requires explicit consent and inventory update. |
| GIS sync / sensor ingestion / upload center | Injected transport contracts or local data/package operations | No configured production Supabase HTTP implementation/credentials found in reviewed app. Sensor ingestion consumes supplied data; upload center prepares locally. Live Supabase auth/RLS remains UNVERIFIED, no silent cloud uploads assumed. |
| Android location/notifications/OCR | GPS provider, local AlarmManager/notifications and bundled OCR models | Local feature paths; GPS requested by user and stops on pause; notifications use user profile. OS location/network behavior is not certified by this review. OCR app wrapper has no cloud request. |
| Development/CI only | GitHub, package indexes, Google/Maven/JitPack/Adoptium | User/developer-triggered dependency resolution and CI/artifact upload; not shipped telemetry. Gradle scan was not enabled. GitHub Actions has contents:read; artifacts are explicit build outputs. |

Evidence: source search for network imports/APIs/URLs and openers; XML namespace
URLs in XLSX/KML are identifiers, not outbound calls. No automatic analytics,
tracking, advertising, diagnostics uploader or kill-switch path was found.
This does not certify every byte of third-party native libraries or OS services.

PROJ API evidence: https://pyproj4.github.io/pyproj/stable/api/network.html
`set_network_enabled(False)` explicitly overrides network configuration.

## Native/transitive continuation — 2026-09-13

The [artifact-level review](PHASE16I_THIRD_PARTY_PRIVACY.md) extends this inventory
without changing application behavior:

| Additional capability / boundary | Data and trigger | Result |
|---|---|---|
| QtNetwork → WinHTTP/system proxy, DNS, Schannel/OpenSSL | Requested host/URL, IP and potentially OS-selected proxy credentials; proxy discovery/PAC and certificate services depend on machine policy while making network requests. | Confirmed import/API capability; no independent background analytics client demonstrated. Machine-specific supporting traffic UNVERIFIED; not limited to the literal tile hostname at OS level. |
| Qt generic TUIO touch plugin | Inbound UDP touch packets, not an outbound telemetry stream; upstream handler binds Any address if external plugin configuration selects it. | Included in inspected Windows bundles. Fieltra does not select it; `QT_QPA_GENERIC_PLUGINS`/Qt launch arguments can. Not evidence of default activation. |
| Windows printing capability | QtPrintSupport can use network printers, but both current application QPrinter sites explicitly select PdfFormat. An external viewer can subsequently print a user-opened file. | General dependency/OS capability, not a newly discovered in-app printer upload. No app NativeFormat/print dialog path found. |
| CPython/OpenSSL/PROJ libcurl; optional installed Qt modules | General socket/TLS/HTTP APIs. PROJ transformer networking remains explicitly off. WebEngine exists in installed Addons but was absent from both inspected packaged bundles. | Capability distinguished from activation. Final Windows artifact membership remains UNVERIFIED; no fresh package built. |
| Tesseract/Leptonica native code | Local Android logs; Leptonica has a debug-gated `system()` path, upstream default off. Tesseract viewer graphics disabled in pinned build. | No direct socket/HTTP imports in the 16 examined native libraries and no new upload demonstrated. Full static/dynamic/native behavior remains UNVERIFIED. |

No newly demonstrated unexpected background outbound behavior required a fix.
No packet capture, network policy change, emulator run or already passing test
was repeated. Native local diagnostic contents and OS/vendor diagnostics are not
covered by the Windows Python log formatter and must not be called fully audited.
