# Third-Party Notices

This file is a source-publication notice and dependency map. It is not a substitute for the complete license texts or a final legal compliance review.

The Mastixa Manager PolyForm Noncommercial project license applies only to original material that the licensor has the right to license. It does **not** override or replace third-party licenses.

## Android

Detailed Android runtime notices are maintained in `android/THIRD_PARTY_NOTICES.md`.

Important bundled/source-tree items include:

- Tesseract4Android / Tesseract OCR and related native components: see `android/THIRD_PARTY_NOTICES.md` and upstream licenses.
- Bundled `ell.traineddata` and `eng.traineddata` OCR models: distributed under their upstream terms; the accompanying license is stored at `android/app/src/main/assets/tessdata/LICENSE`.
- JTS, Proj4J / Proj4J-EPSG, GeographicLib-Java and EPSG-derived CRS data: see `android/THIRD_PARTY_NOTICES.md` and the applicable upstream/EPSG terms.
- Gradle wrapper files under `android/gradle/wrapper/` remain subject to Gradle's upstream licensing and distribution terms.

## Windows / Python source dependencies

The project source references or builds with third-party software including PySide6 / Qt, pyproj / PROJ, Shapely / GEOS, NumPy and other Python packages listed by the project requirements and build tooling. Those packages are not relicensed under PolyForm Noncommercial by this repository.

A detailed engineering inventory is available in `docs/PHASE16I_LICENSE_READINESS.md`. That document records identified licenses and remaining distribution-readiness work; it explicitly is not legal clearance.

In particular, public **binary** redistribution has separate obligations from publishing this source snapshot. The current Windows bundle previously required special attention to Qt Virtual Keyboard and comprehensive third-party notice delivery. Publishing source code does not by itself clear those binary-distribution obligations.

## Assets and branding

Tracked UI icons, branding artwork, ICO/PNG/SVG assets and other media require confirmed authorship or redistribution rights before they should be treated as covered first-party material in a public source repository. The project has AI-assisted, project-specific icon work, but a complete per-file provenance ledger for every tracked legacy/branding asset has not yet been closed.

Do not assume that absence of a separate notice means a third-party asset is covered by the project license.

## General rule

Where a file contains its own license or copyright notice, that notice controls for that file. Recipients are responsible for complying with all applicable third-party terms when building, modifying, or redistributing the project or binaries produced from it.