"""Bounded file import. No network access, archive extraction or XML entities."""
from __future__ import annotations
import io
import json
from pathlib import Path
import zipfile
from defusedxml import ElementTree as ET
from .geometry import normalize, crs_name

MAX_BYTES = 10 * 1024 * 1024


def _combine(polygons):
    if not polygons:
        raise ValueError("Δεν βρέθηκαν πολύγωνα / No polygons")
    return ({"type": "Polygon", "coordinates": polygons[0]} if len(polygons) == 1
            else {"type": "MultiPolygon", "coordinates": polygons})


def import_geometry(data: bytes, filename: str, declared_crs: str = ""):
    if len(data) > MAX_BYTES:
        raise ValueError("Το αρχείο υπερβαίνει τα 10 MB / File exceeds 10 MB")
    extension = Path(filename).suffix.lower()
    if extension in {".json", ".geojson"}:
        value = json.loads(data.decode("utf-8-sig"))
        embedded = value.get("crs", {}).get("properties", {}).get("name", "")
        source = declared_crs or embedded or "EPSG:4326"
        if declared_crs and embedded and crs_name(declared_crs) != crs_name(embedded):
            raise ValueError("Το δηλωμένο CRS διαφέρει από το αρχείο / CRS conflict")
        if value.get("type") == "FeatureCollection":
            if len(value.get("features", [])) != 1:
                raise ValueError("Επίλεξε αρχείο με ένα Feature / Exactly one feature required")
            value = value["features"][0]
        if value.get("type") == "Feature":
            value = value["geometry"]
        return normalize(value, source)
    if extension == ".kml":
        if declared_crs and crs_name(declared_crs) != "EPSG:4326":
            raise ValueError("KML uses WGS84 longitude/latitude")
        root = ET.fromstring(data)
        polygons = []
        for polygon in root.iter():
            if polygon.tag.split("}")[-1] != "Polygon":
                continue
            rings = []
            for boundary in ("outerBoundaryIs", "innerBoundaryIs"):
                for node in polygon.findall("{*}" + boundary):
                    coords = node.find(".//{*}coordinates")
                    if coords is None:
                        raise ValueError("Missing KML coordinates")
                    ring = []
                    for token in (coords.text or "").split():
                        xyz = [float(v) for v in token.split(",")]
                        if len(xyz) not in {2, 3} or (len(xyz) == 3 and xyz[2] != 0):
                            raise ValueError("Only 2D/zero-altitude cadastral KML supported")
                        ring.append(xyz[:2])
                    rings.append(ring)
            polygons.append(rings)
        return normalize(_combine(polygons), "EPSG:4326")
    if extension in {".gml", ".xml"}:
        root = ET.fromstring(data)
        polygons, sources = [], set()
        inherited = root.get("srsName", "")
        for polygon in root.iter():
            if polygon.tag.split("}")[-1] != "Polygon":
                continue
            srs = polygon.get("srsName", inherited) or declared_crs
            if not srs:
                raise ValueError("GML requires an explicit source CRS")
            source = crs_name(srs)
            if declared_crs and source != crs_name(declared_crs):
                raise ValueError("GML CRS conflict")
            sources.add(source)
            rings = []
            for boundary in ("exterior", "interior"):
                for node in polygon.findall("{*}" + boundary):
                    pos = node.find(".//{*}posList")
                    if pos is None or pos.get("srsDimension", polygon.get("srsDimension", "2")) != "2":
                        raise ValueError("GML supports 2D posList rings only")
                    numbers = [float(x) for x in (pos.text or "").split()]
                    if len(numbers) % 2:
                        raise ValueError("Odd GML coordinate count")
                    pairs = [numbers[n:n+2] for n in range(0, len(numbers), 2)]
                    # GML EPSG axis order is authority-defined, unlike GeoJSON XY.
                    from pyproj import CRS
                    if CRS(source).axis_info[0].direction in {"north", "south"}:
                        pairs = [[y, x] for x, y in pairs]
                    rings.append(pairs)
            polygons.append(rings)
        if len(sources) != 1:
            raise ValueError("GML must use one known CRS")
        return normalize(_combine(polygons), sources.pop())
    if extension == ".zip":
        import shapefile
        with zipfile.ZipFile(io.BytesIO(data)) as archive:
            members = archive.infolist()
            if len(members) > 20 or sum(m.file_size for m in members) > MAX_BYTES:
                raise ValueError("Shapefile archive exceeds limits")
            if any("/" in m.filename or "\\" in m.filename for m in members):
                raise ValueError("Shapefile ZIP must have flat file names")
            names = [m.filename for m in members if m.filename.lower().endswith(".shp")]
            if len(names) != 1:
                raise ValueError("ZIP must contain exactly one Shapefile")
            stem = names[0][:-4]
            lookup = {m.filename.lower(): m.filename for m in members}
            if len(lookup) != len(members):
                raise ValueError("Duplicate ZIP members")
            def member(ext):
                name = lookup.get((stem + ext).lower())
                return archive.read(name) if name else None
            prj = member(".prj")
            source = crs_name(prj.decode() if prj else declared_crs)
            if declared_crs and source != crs_name(declared_crs):
                raise ValueError("Shapefile CRS conflict")
            reader = shapefile.Reader(shp=io.BytesIO(member(".shp")),
                                      dbf=io.BytesIO(member(".dbf")) if member(".dbf") else None)
            shapes = reader.shapes()
            if len(shapes) != 1 or shapes[0].shapeType != shapefile.POLYGON:
                raise ValueError("Shapefile must contain one 2D polygon record")
            return normalize(shapes[0].__geo_interface__, source)
    if extension == ".dxf":
        import ezdxf
        if not declared_crs:
            raise ValueError("DXF requires its actual source EPSG CRS")
        document = ezdxf.read(io.StringIO(data.decode("utf-8-sig")))
        polygons = []
        for entity in document.modelspace():
            if entity.dxftype() != "LWPOLYLINE" or not entity.closed:
                raise ValueError("DXF: only closed straight 2D LWPOLYLINE entities supported")
            if entity.dxf.elevation != 0 or tuple(entity.dxf.extrusion) != (0, 0, 1):
                raise ValueError("DXF: only XY plane supported")
            coords = []
            for x, y, _start, _end, bulge in entity.get_points():
                if bulge:
                    raise ValueError("DXF arcs must be converted to authorized polygon vertices first")
                coords.append([x, y])
            if coords and coords[0] != coords[-1]:
                coords.append(coords[0].copy())
            polygons.append([coords])
        return normalize(_combine(polygons), declared_crs)
    raise ValueError("Υποστηρίζονται GeoJSON, KML, GML posList, Shapefile ZIP, DXF LWPOLYLINE")
