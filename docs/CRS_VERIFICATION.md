# Phase 5 reference verification

Both clients consume the same `shared/fixtures/crs_reference.json`.
Published references are from the primary [pyproj examples](https://pyproj4.github.io/pyproj/stable/examples.html)
and [PROJ Greek datum-shift example](https://proj.org/en/stable/usage/transformation.html).
The Greek Grid point is additionally a cross-library comparison: PROJ 9.8.1 /
pyproj 3.8.0 output, checked independently by Proj4J 1.4.3.

Tolerances are numerical reference tolerances: 1 mm for the published Web
Mercator example, 2 cm for UTM, and 2e-7 degrees for the Greek references (the
published datum example is rounded to 0.001 arcsecond). Reverse tolerances are
explicit per case, including 3 cm for Greek Grid. None is a claim of survey/GNSS
measurement accuracy or of the live Cadastre service's CRS.

Tests cover forward/reverse transforms, X/Y versus latitude/longitude, deliberate
axis swap detection, source precision/order, repeated closure removal and rejection
of unknown/3D/geocentric systems. Source coordinates remain untouched; WGS84 is
a separate copy. Android found a real bug: Proj4J accepted EPSG:4978 despite the
2D input contract. A compact EPSG metadata catalog (PROJ 9.8.1, EPSG v12.029)
now rejects incompatible dimensions/units/axes before projection. It contains
6,278 eligible 2D east/north CRS identifiers, geographic coordinates in degrees.
The transformation itself still uses Proj4J; no homemade datum/projection formula
was introduced. Unsupported configurations can be converted on Desktop.

- Desktop `python -m unittest tests.test_crs_reference -v`: 2 passed, 0.089s.
- Android initial reference run: published numeric cases passed; incompatible-CRS
  test failed as expected on the discovered bug.
- After the actual fix, Android CRS/geometry/import/export suite: **10 passed,
  4.393s**, `/sdcard/mastixa-crs-final-tests.txt`; build/lint passed (8s).
- Existing assertions/tolerances were retained; no failed reference was adjusted.
