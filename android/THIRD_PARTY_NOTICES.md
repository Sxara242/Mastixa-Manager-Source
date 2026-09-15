# Offline OCR

Tesseract4Android 4.9.0, Copyright 2019 Adaptech s.r.o., Robert Pösel. Apache License 2.0. Dependency pinned in app/build.gradle; JitPack restricted to its group.
Source and license: https://github.com/adaptech-cz/Tesseract4Android
Upstream wrapper credits: tess-two and Tesseract Tools for Android.
Native components per the upstream README: Tesseract 5.5.1, Leptonica 1.85.0, libjpeg v9f, libpng 1.6.48, each under its upstream license. See the dependency repository for their source and notices.

Bundled language models from https://github.com/tesseract-ocr/tessdata_fast (main), downloaded 2026-09-08. Apache License 2.0; full license is app/src/main/assets/tessdata/LICENSE and ships in the APK. Models are distributed with the app to make first use offline.

- ell.traineddata SHA-256: 4fba8a0b461038d51f1c20d043d4f2ac38c4e778f1b90830847f7bd8fa3ba726
- eng.traineddata SHA-256: 7d4322bd2a7749724879683fc3912cb542f19906c83bcc1a52132556427170b2

OCR input stays on the device. Internet permission is used for explicitly selected
online map tiles; OCR itself performs no network request.

# Geometry libraries

- LocationTech JTS 1.20.0: polygon topology and containment. Upstream source and
  license: https://github.com/locationtech/jts (EPL 2.0 / EDL 1.0).
- LocationTech Proj4J and Proj4J-EPSG 1.4.3: coordinate transformation and EPSG
  definitions. https://github.com/locationtech/proj4j (Apache 2.0 and EPSG dataset
  distribution terms; see upstream LICENSE).
- GeographicLib-Java 2.1: WGS84 ellipsoidal area and perimeter.
  https://github.com/geographiclib/geographiclib-java (MIT/X11).

These dependencies perform local geometry calculations; they do not send parcel
coordinates or GPS information to a service.

The compact `crs-2d.txt` catalog records dimensional/axis eligibility derived from
the EPSG database distributed with PROJ via pyproj. Its header identifies the
PROJ/EPSG version. CRS identifiers remain EPSG identifiers; this filtered catalog
does not replace or modify the official definitions or infer the Cadastre service
CRS. Definitions and calculations remain in Proj4J. See https://proj.org/about.html
and the EPSG distribution terms shipped by Proj4J-EPSG.
