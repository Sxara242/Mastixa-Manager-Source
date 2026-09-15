# Phase 16I — third-party privacy inventory

Evidence: requirements.txt, installed distribution metadata, app imports, Gradle
`dependencies --configuration debugRuntimeClasspath` (successful), manifest,
OfflineOcr and geometry/network wrappers. Versions below describe reviewed local
resolution, not a promise about all future versions allowed by requirements.
No telemetry/analytics/advertising/crash-upload SDK found in the runtime graph.
**Not found is not proof of impossibility inside all transitive native code.**

| Dependency / reviewed version | Purpose | Network capability | Telemetry / analytics / cloud crash capability | Privacy status / evidence |
|---|---|---|---|---|
| PySide6, Essentials, Addons, shiboken6 6.11.2 / Qt | Windows UI, rendering, PDF, network cache | QtNetwork; other optional Qt modules also capable | No such SDK/API use found; autonomous behavior of all bundled native plugins UNVERIFIED | PARTIAL: imports and packaging spec reviewed, no binary/source-complete certification. Only selected OSM path used. |
| pyproj 3.8.0 / PROJ / certifi | CRS transforms, geodesic operations, trust bundle | PROJ can download grids; now explicitly disabled for transformers | No analytics/crash uploader found; remote grids are functional network, not telemetry | PASS for enforced offline transformer setting with hostile environment + reference tests; native supply-chain assurance UNVERIFIED. [API](https://pyproj4.github.io/pyproj/stable/api/network.html). |
| Shapely 2.1.2 / GEOS / NumPy | Local geometry/numerics | No app-requested network path | None found in integration; native binary internals UNVERIFIED | PARTIAL: local-only usage, no tracking SDK dependency. |
| pyshp 2.4.2 | Shapefile parsing | Library can support URL input; app supplies bounded in-memory archive members | None found in integration | PASS for local call boundary; upstream-wide absence UNVERIFIED. |
| ezdxf 1.4.4, pyparsing, typing_extensions, fonttools, NumPy | DXF/local parsing | Optional library functionality not all audited; app uses local input | None found in integration | PARTIAL: no app outbound path; optional/transitive functionality not certified. |
| defusedxml 0.7.1 | XML entity protection | App uses protected local parse | No analytics/telemetry/crash integration found | PASS for chosen safe parser usage; not a whole-package security certification. |
| openpyxl 3.1.5 / et-xmlfile | XLSX export | No app network path | None found in integration | PASS for local export use; external spreadsheet viewer behavior outside app scope. |
| JTS core 1.20.0 | Android geometry | No network service in runtime graph/use | No telemetry/analytics/crash SDK found | PARTIAL: graph and usage reviewed, complete jar internals UNVERIFIED. |
| Proj4J / EPSG 1.4.3 | Android CRS + bundled definitions | No grid-download integration found | None found | PARTIAL: local usage/graph, full binary audit UNVERIFIED. |
| GeographicLib-Java 2.1 | Android geodesics | No app network path | None found | PARTIAL: usage/graph verified, upstream-wide absence UNVERIFIED. |
| Tesseract4Android 4.9.0 + native Tesseract/Leptonica/image codecs | Offline OCR | Wrapper reads bundled models/private files; no app cloud call | No analytics/crash SDK in resolved graph; all native code UNVERIFIED | PARTIAL: OfflineOcr inspected; [upstream architecture](https://github.com/adaptech-cz/Tesseract4Android) describes native OCR and local tessdata. Do not infer pinned binary internals from latest README. |
| AndroidX annotation 1.3.0 | Tesseract annotation dependency | No runtime service configured | No SDK for telemetry etc. | PASS for graph role; no startup component introduced in source manifest. |
| desugar_jdk_libs 2.1.5 | Java API compatibility | General Java APIs may include networking | No analytics/crash service configured | PARTIAL: compatibility runtime is not a telemetry SDK, complete implementation UNVERIFIED. |
| Android framework / SQLite / PDF/image decoders | OS storage, providers, location, decoding | OS/providers can network independently | Vendor OS diagnostics not controlled by Fieltra | UNVERIFIED beyond application permission/call boundaries. |
| PyInstaller, Inno, Gradle/AGP, JDK, AndroidX runner, JUnit | Build/test only | Dependency downloads/CI | No application telemetry dependency added | Separate tooling boundary; no Gradle scan enabled. Test libraries do not appear in debugRuntimeClasspath. |

No dependency was removed without evidence of an unnecessary tracking component.
No full native binary review, packet capture, historical dependency audit or CVE
certification was performed. Requirements use version ranges; a future resolution
must repeat this inventory before release. Repository has no root distribution
license; only the OCR asset license was found by license-file inventory. Licensing
and redistribution obligations are now assessed in
[License / distribution readiness](PHASE16I_LICENSE_READINESS.md).
No license or signing strategy changed here.

## Native / transitive privacy assurance — 2026-09-13 continuation

Baseline: `bcedfeea02bb40bfa9032427127ec1cbf1a16aaa`, CI #144 SUCCESS
for both jobs (read-only GitHub confirmation; no new run). This is a static,
artifact-specific assurance review, not a repeat of the 23 passing tests.
PASS below applies to a stated boundary, never to every byte of a library.

### Evidence and artifact boundary

- Installed Windows wheel metadata/RECORD/license files were enumerated in
  `.venv/Lib/site-packages`: Python 3.12.14, SQLite 3.53.1, versions in the table
  above. Native wheel tags: pyproj/Shapely/NumPy `cp312-cp312-win_amd64`,
  PySide6 Essentials/Addons `cp310-abi3-win_amd64`. These are installed wheel
  contents, not independently authenticated downloads or reproducible builds.
- Existing `dist/MastixaManager` (2026-08-29) contains 117 PE files;
  `.tools/phase8-packaged-dist/MastixaManager` (2026-09-10) contains 173.
  The latter's PE normal/delay imports and SHA-256 values were inspected.
  Neither is a Windows package built from the current HEAD. The current spec
  and installed PyInstaller Qt hook configuration were also read. A final
  Windows release's exact component inventory remains UNVERIFIED; no rebuild
  was justified for this documentation-only audit. CI uses a different Python
  installation, so local wheel provenance is not silently attributed to CI.
- Existing runner checkout HEAD was read as `bcedfee`; its existing debug APK
  SHA-256 is `549d5dc11514b7a9ffd393ff7eea40eb7f22bc1763535c3fd42c5d74a68c7696`.
  All **16/16** native members equal the cached Tesseract AAR members byte for
  byte. These are artifact comparisons, not runtime tests.
- Resolved Android graph from the previous review is retained. Cached JAR/AAR
  contents/POMs were inspected: JTS 732 classes, Proj4J 162, GeographicLib 18,
  Tesseract wrapper 41, annotation 1.3.0 66; Proj4J-EPSG is data (0 classes).
  None of these 1,019 class files contains the inspected direct Java network or
  selected analytics/crash-SDK references (`java/net`, `javax/net`, okhttp,
  Firebase/Crashlytics, Google Play services, Sentry). This limited constant-pool
  scan cannot rule out reflection, obfuscation, JNI or every possible SDK.
  Annotation 1.7.0-beta01 also exists in the cache, but is not promoted into the
  runtime inventory merely because it is cached.
- The APK's DEX files had no inspected Firebase/Crashlytics/Sentry/Facebook Ads/
  Segment markers. The AAR manifest adds only package/minSdk, no permissions,
  components or automatic initializer. APK contains only the four OCR library
  names across arm64-v8a, armeabi-v7a, x86, x86_64; no other `.so` appeared.
- ELF dynamic undefined symbols were inspected across all 16 OCR binaries.
  No direct `socket`, `connect`, `getaddrinfo`, libcurl or SSL imports appeared.
  Leptonica imports `system` and Android local logging; Tesseract imports local
  logging/assert and `sendfile` (a file-descriptor operation, not proof of an
  HTTP client). Absence of imports is not proof against raw syscalls/static code.
- Upstream source was read at Tesseract4Android **4.9.0** and Qt **v6.11.2**,
  rather than assuming latest README describes pinned binaries. Local inspection
  evidence under ignored `.tools/phase16i-*` contains no business data; it is not
  an application artifact and must not be shipped.

### Native and transitive findings by component

The telemetry/analytics/advertising/automatic crash-upload column concerns those
capabilities together; no identifier-collection client was found in these paths.
OS diagnostic collection remains outside this statement.

| Component / purpose | Network, background behavior and activation | Telemetry / analytics / automatic upload evidence | Status |
|---|---|---|---|
| Qt Core/Gui/Widgets/PrintSupport, QML/Quick/OpenGL/SVG; UI/rendering | PE imports include Winsock in Core and QtNetwork dependencies through plugins. Core socket capability is not evidence of outbound startup traffic. Qt can use network printers; both current app QPrinter sites select PdfFormat, so direct network printing is not an active app path. | No collector/SDK found; full Qt/native source-to-binary correspondence not established. | PARTIAL; whole-binary absence UNVERIFIED |
| QtNetwork, networkinformation, TLS Schannel/OpenSSL plugins; map HTTP | Confirmed DNSAPI, Winsock, WinHTTP proxy and Secur32 imports. OSM is the existing explicit app path. System proxy/PAC discovery and OS TLS certificate services may create supporting traffic, depending on machine policy. No new independent uploader demonstrated. | No analytics/crash pipeline in Fieltra configuration. Proxy authentication can expose OS-selected credentials to a configured proxy; not an app tracking identifier. | PARTIAL; machine-specific traffic UNVERIFIED |
| Qt generic `qtuiotouchplugin` | Additional **inbound** UDP capability: upstream `QTuioHandler` binds Any address when the plugin is selected. Qt startup accepts `QT_QPA_GENERIC_PLUGINS`/plugin arguments. Fieltra does not configure it. Not evidence of default background outbound networking. | Remote touch input capability, not telemetry. External launch environment can activate optional Qt functionality. | PARTIAL; recorded deployment risk, not a reproduced default app bug |
| Qt VirtualKeyboard, PDF/PDFium, imageformat plugins, software OpenGL | Included by automatic QtGui plugin collection in inspected packages; no WebEngineCore/QtWebEngineProcess in either package. Installed Addons does contain WebEngine/Positioning/NetworkAuth, which must not be mistaken for shipped components. | Optional WebEngine has broad browser capability; not enabled by Fieltra and not present in inspected bundles. PDFium/codec internals not fully certified. | PARTIAL privacy; VirtualKeyboard licensing issue below |
| pyproj/PROJ + bundled libcurl, SQLite, TIFF, JPEG, zlib, lzma | Confirmed PROJ → curl easy API → Winsock/SSPI import chain. Explicit offline transformer setting and prior regression remain PASS. Optional upstream sync/download helpers are not called by Fieltra. | Functional grid download capability, not evidence of analytics. No new bypass of the offline transformer boundary found. | PASS boundary; binary assurance UNVERIFIED |
| Shapely/GEOS + NumPy/OpenBLAS/LAPACK/GCC runtime | Geometry/numerics; inspected DLLs did not directly import the selected network DLLs. CPU-feature/SIMD detection is local computation, not a tracking upload. | No collector found. Static-link/transitive code and binary provenance remain incompletely verified. | PARTIAL |
| ezdxf native accelerators, fontTools, pyparsing, typing_extensions, pyshp, defusedxml, openpyxl/et-xmlfile | Local CAD/shape/XML/XLSX/font processing. Pyshp URL capability stays outside the app's memory-buffer boundary. No new integration path found. | None found in reviewed integration/metadata; optional whole-package features not exhaustively audited. | PASS local boundary; package-wide assurance PARTIAL |
| CPython and extension modules, OpenSSL, libffi, expat, compression; SQLite | General socket/TLS/process capability exists in `_socket`, `_ssl`, select, overlapped, multiprocessing and OpenSSL; confirmed in PE imports. Both CPython SQLite and PROJ's separate SQLite are local engines in app use. Extension loading/untrusted SQL is not enabled by this audit. | No automatic application uploader configured. Windows WER/OS behavior is separate. | PARTIAL; OS/runtime internals UNVERIFIED |
| Microsoft CRT/UCRT/API-set DLLs, Windows drivers/certificate services | Platform runtime; potential OS networking/diagnostics cannot be certified by application inspection. | Not an app analytics SDK; vendor OS policy outside app control. | UNVERIFIED at OS boundary |
| Android JTS/Proj4J/EPSG/GeographicLib | Local Java geometry and definitions. No direct Java network references in the inspected 912 geometry classes. | No collectors or automatic components found. | PASS inspected direct-call boundary; whole binary UNVERIFIED |
| Tesseract4Android wrapper / Tesseract 5.5.1 | Local Bitmap/Pix recognition, bundled models. Pinned CMake sets `GRAPHICS_DISABLED`, excluding the debug viewer network path. Standard variant, not OpenMP. Native source includes local initialization-language/error logs. | No manifest initializer, Java HTTP reference or native socket import found; local logs do not equal automatic upload. All exceptional log values not exhaustively certified. | PARTIAL; no demonstrated privacy violation |
| Leptonica 1.85.0 | Pinned `utils2.c` gates `system()` behind `LeptDebugOK`; pinned `writefile.c` initializes that flag to 0. Fieltra does not enable it; JNI initialization inspected. No exploitation or external command was executed. | Debug capability is real but not demonstrated active in the OCR path. No direct network imports found. | PARTIAL; not classified as a live command-execution bug |
| libjpeg v9f / libpng 1.6.48, Android zlib, C++ support | Local codecs; no network imports in the eight jpeg/png binary members. NDK 27.2.12479018 in upstream build; C++ symbols may be statically linked, with no separate libc++_shared.so in APK. Exact static source closure UNVERIFIED. | No uploader found. Malformed-image security is not certified by import scanning. | PARTIAL |
| AndroidX annotation 1.3.0 | 66 annotation/support classes; no network reference/component. | No initializer or telemetry service. | PASS inspected role |
| desugar_jdk_libs 2.1.5 | 1,459 cached compatibility classes include URI/file and socket-channel APIs. D8 selects/rewrites required classes; entire input JAR is not presumed shipped. No standalone background service. | No app telemetry activation; full DEX reachability not proved. | PARTIAL |
| Android framework LocationManager, SQLite, PdfRenderer, SAF, HTTP | No separate Play services location SDK, Room, OkHttp or map SDK in runtime graph. OS supplies APIs; SAF/network printer/cloud provider behavior remains user/OS controlled. | OS/vendor diagnostics and assisted-location traffic are not certified. | PASS app boundary; OS UNVERIFIED |
| PyInstaller bootloader/hooks, Inno setup/uninstaller | Executable loader and installer code are redistributed; build tools as a whole are not. Inspected spec adds no runtime hook/uploader. Hooks can add optional libraries automatically. | No app analytics pipeline found. Complete bootloader/compiler supply chain not reproducibly verified. | PARTIAL |

Pinned evidence:
[Qt TUIO source](https://github.com/qt/qtbase/blob/v6.11.2/src/plugins/generic/tuiotouch/qtuiohandler.cpp),
[Qt plugin activation](https://github.com/qt/qtbase/blob/v6.11.2/src/gui/kernel/qguiapplication.cpp),
[Qt proxy API](https://doc.qt.io/qt-6/qnetworkproxyfactory.html),
[OCR native build](https://github.com/adaptech-cz/Tesseract4Android/blob/4.9.0/tesseract4android/src/main/cpp/tesseract/CMakeLists.txt),
[Leptonica command guard](https://github.com/adaptech-cz/Tesseract4Android/blob/4.9.0/tesseract4android/src/main/cpp/leptonica/src/src/utils2.c),
[Leptonica default](https://github.com/adaptech-cz/Tesseract4Android/blob/4.9.0/tesseract4android/src/main/cpp/leptonica/src/src/writefile.c).

### Artifact fingerprints

| Cached resolved input | SHA-256 |
|---|---|
| Tesseract4Android 4.9.0 AAR | `bce5d6413a1a5ae3d7240033fbbc851ba3217d0a08d9769400e17a077f42cb2a` |
| JTS core 1.20.0 JAR | `6a783d8f9dba3d3cf7265435f134402f63c05838aa6cbcc4297ad3a5b2842baf` |
| Proj4J 1.4.3 JAR | `20c0adda4c784f88be9694a93a2bee15c00ea6290b13645f8295400d1cd365d2` |
| Proj4J-EPSG 1.4.3 JAR | `82b027e3d2b6bf7f51572d9d8c46fc2c049fabc03d63f5815cc7aec9e319071f` |
| GeographicLib-Java 2.1 JAR | `1e85feac761b436309a8d3d2ece07162129fd5670afbf1d2d435e38006da00dd` |
| AndroidX annotation 1.3.0 JAR | `97dc45afefe3a1e421da42b8b6e9f90491477c45fc6178203e3a5e8a05ee8553` |
| desugar_jdk_libs 2.1.5 JAR | `d8044befae095781b9a80bf1faa92edc30382d75d437476784c1bf991598a976` |

These identify inspected inputs, not a lockfile, signature verification or a
guarantee of provenance. No native reproducible rebuild, packet capture, full
decompilation, raw-syscall analysis, independent CVE audit or production OS
certification was performed. No newly demonstrated unexpected background upload
requires application changes. Remaining theoretical inability to prove every byte
is **UNVERIFIED**, not by itself a release blocker. Concrete licensing/notices
gaps, however, are real distribution-readiness blockers.
