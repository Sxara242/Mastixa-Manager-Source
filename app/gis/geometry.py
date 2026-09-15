"""Ordered polygon geometry. GeoJSON coordinates always use X/Y (longitude/latitude).

Original coordinates are retained verbatim; normalization never repairs/reorders
the source. This parcel workflow rejects antimeridian and continental geometry.
"""
from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache
import json
import math

from pyproj import CRS, Geod, Transformer, network
from shapely.geometry import Point, shape, mapping
from shapely.ops import transform
from shapely.validation import explain_validity

MAX_VERTICES = 20_000
GEOD = Geod(ellps="WGS84")


@lru_cache(maxsize=32)
def transformer(source: str, target: str) -> Transformer:
    # Local CRS operations must never silently download grids, even via environment settings.
    network.set_network_enabled(False)
    return Transformer.from_crs(CRS(source), CRS(target), always_xy=True,
                                allow_ballpark=False)


def crs_name(value: str) -> str:
    if not value or len(value) > 10_000:
        raise ValueError("Δήλωσε το πραγματικό σύστημα συντεταγμένων / Source CRS required")
    crs = CRS.from_user_input(value)
    code = crs.to_epsg()
    if code is None or not (crs.is_geographic or crs.is_projected) or len(crs.axis_info) != 2:
        raise ValueError("Απαιτείται δισδιάστατο EPSG CRS / A 2D EPSG CRS is required")
    return f"EPSG:{code}"


def parts(geometry: dict):
    kind = geometry.get("type")
    if kind not in {"Polygon", "MultiPolygon"}:
        raise ValueError("Μόνο Polygon / MultiPolygon")
    values = geometry.get("coordinates")
    if not isinstance(values, list) or not values:
        raise ValueError("Κενή γεωμετρία / Empty geometry")
    return [values] if kind == "Polygon" else values


def vertices(geometry: dict):
    """One-based part/ring/vertex; ring 1 is exterior, remaining rings are holes."""
    for part_id, polygon in enumerate(parts(geometry), 1):
        for ring_id, ring in enumerate(polygon, 1):
            for index, coordinate in enumerate(ring[:-1], 1):
                yield part_id, ring_id, index, coordinate[0], coordinate[1]


def validate(geometry: dict):
    count = 0
    for polygon in parts(geometry):
        if not isinstance(polygon, list) or not polygon:
            raise ValueError("Empty polygon")
        for ring in polygon:
            if not isinstance(ring, list) or len(ring) < 4 or ring[0] != ring[-1]:
                raise ValueError("Κάθε δακτύλιος χρειάζεται 3 κορυφές και κλείσιμο / Unclosed ring")
            count += len(ring) - 1
            if count > MAX_VERTICES:
                raise ValueError("Πάρα πολλές κορυφές / Too many vertices")
            for position in ring:
                if (not isinstance(position, list) or len(position) != 2
                        or any(isinstance(v, bool) or not isinstance(v, (int, float))
                               or not math.isfinite(v) for v in position)):
                    raise ValueError("Μη έγκυρες δισδιάστατες συντεταγμένες / Invalid XY")
            if any(a == b for a, b in zip(ring, ring[1:])):
                raise ValueError("Διαδοχική διπλή κορυφή / Duplicate adjacent vertex")
    result = shape(geometry)
    if result.is_empty or not result.is_valid or result.area <= 0:
        raise ValueError("Μη έγκυρο πολύγωνο / Invalid polygon: " + explain_validity(result))
    return result


@dataclass(frozen=True)
class ParcelGeometry:
    original: dict
    source_crs: str
    wgs84: dict
    area_m2: float
    perimeter_m: float
    centroid_lon: float
    centroid_lat: float
    bbox: tuple

    @property
    def vertex_count(self):
        return sum(1 for _ in vertices(self.original))

    def contains(self, lon: float, lat: float) -> bool:
        check_position(lon, lat)
        return shape(self.wgs84).covers(Point(lon, lat))


def check_position(lon, lat):
    if not (math.isfinite(lon) and math.isfinite(lat) and -180 <= lon <= 180 and -90 <= lat <= 90):
        raise ValueError("Invalid WGS84 longitude/latitude")


def normalize(geometry: dict, source_crs: str) -> ParcelGeometry:
    source = crs_name(source_crs)
    original = json.loads(json.dumps(geometry, allow_nan=False))
    source_shape = validate(original)
    normalized = transform(transformer(source, "EPSG:4326").transform, source_shape)
    # mapping uses tuples; canonical JSON arrays are required by the shared contract.
    wgs = json.loads(json.dumps(mapping(normalized), allow_nan=False))
    validate(wgs)
    for _, _, _, lon, lat in vertices(wgs):
        check_position(lon, lat)
    bbox = normalized.bounds
    if bbox[2]-bbox[0] > 5 or bbox[3]-bbox[1] > 5 or max(abs(bbox[1]), abs(bbox[3])) > 85:
        raise ValueError("Geometry exceeds local parcel scope (5 degrees / polar / antimeridian)")
    area = perimeter = 0.0
    for polygon in parts(wgs):
        for index, ring in enumerate(polygon):
            a, p = GEOD.polygon_area_perimeter([v[0] for v in ring], [v[1] for v in ring])
            area += abs(a) if index == 0 else -abs(a)
            perimeter += p  # includes hole boundaries, consistently on both platforms
    if not math.isfinite(area) or area <= 0:
        raise ValueError("Invalid geodesic area")
    projected = transform(transformer("EPSG:4326", "EPSG:3857").transform, normalized)
    center = projected.centroid
    lon, lat = transformer("EPSG:3857", "EPSG:4326").transform(center.x, center.y)
    return ParcelGeometry(original, source, wgs, area, perimeter, lon, lat, bbox)


def manual_coordinates(text: str, source_crs: str) -> ParcelGeometry:
    rows = []
    for line in text.splitlines():
        if line.strip():
            values = line.replace(";", " ").replace(",", " ").split()
            if len(values) != 2:
                raise ValueError("Κάθε γραμμή: X Y ή longitude latitude, τελεία δεκαδικών")
            rows.append([float(x) for x in values])
    if rows and rows[0] != rows[-1]:
        rows.append(rows[0].copy())
    return normalize({"type": "Polygon", "coordinates": [rows]}, source_crs)
