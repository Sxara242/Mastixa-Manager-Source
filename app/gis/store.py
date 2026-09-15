"""Additive GIS migration and profile-local transactions; no provider or UI code."""
from __future__ import annotations
import json
import time
import uuid
from .geometry import normalize, check_position


def migrate(connection):
    connection.executescript("""
        CREATE TABLE IF NOT EXISTS parcel_geometry(
            id TEXT PRIMARY KEY,
            field_id INTEGER UNIQUE REFERENCES fields(id) ON DELETE SET NULL,
            name TEXT NOT NULL, kaek TEXT NOT NULL,
            original_geojson TEXT NOT NULL, source_crs TEXT NOT NULL,
            wgs84_geojson TEXT NOT NULL,
            area_m2 REAL NOT NULL CHECK(area_m2>0),
            perimeter_m REAL NOT NULL CHECK(perimeter_m>0),
            centroid_lon REAL NOT NULL, centroid_lat REAL NOT NULL,
            bbox TEXT NOT NULL, geometry_source TEXT NOT NULL,
            geometry_source_date TEXT NOT NULL,
            created_at INTEGER NOT NULL, updated_at INTEGER NOT NULL,
            deleted_at INTEGER, last_sync_at INTEGER,
            revision INTEGER NOT NULL CHECK(revision>0)
        );
        CREATE TABLE IF NOT EXISTS geo_points(
            id TEXT PRIMARY KEY, parcel_id TEXT NOT NULL REFERENCES parcel_geometry(id),
            point_type TEXT NOT NULL, title TEXT NOT NULL, notes TEXT NOT NULL,
            longitude REAL NOT NULL CHECK(longitude BETWEEN -180 AND 180),
            latitude REAL NOT NULL CHECK(latitude BETWEEN -90 AND 90),
            accuracy REAL NOT NULL CHECK(accuracy>=0),
            created_at INTEGER NOT NULL, updated_at INTEGER NOT NULL,
            deleted_at INTEGER, last_sync_at INTEGER,
            revision INTEGER NOT NULL CHECK(revision>0)
        );
        CREATE INDEX IF NOT EXISTS idx_geo_points_parcel ON geo_points(parcel_id,deleted_at);
        CREATE TABLE IF NOT EXISTS geo_tracks(
            id TEXT PRIMARY KEY, parcel_id TEXT NOT NULL REFERENCES parcel_geometry(id),
            title TEXT NOT NULL, positions_json TEXT NOT NULL,
            started_at INTEGER NOT NULL, ended_at INTEGER,
            duration_ms INTEGER NOT NULL CHECK(duration_ms>=0),
            distance_m REAL NOT NULL CHECK(distance_m>=0),
            created_at INTEGER NOT NULL, updated_at INTEGER NOT NULL,
            deleted_at INTEGER, last_sync_at INTEGER,
            revision INTEGER NOT NULL CHECK(revision>0)
        );
        CREATE INDEX IF NOT EXISTS idx_geo_tracks_parcel ON geo_tracks(parcel_id,deleted_at);
        CREATE TABLE IF NOT EXISTS gis_changes(
            id TEXT PRIMARY KEY, entity TEXT NOT NULL, entity_id TEXT NOT NULL,
            revision INTEGER NOT NULL, created_at INTEGER NOT NULL
        );
        CREATE TRIGGER IF NOT EXISTS gis_field_delete
        BEFORE DELETE ON fields BEGIN
            UPDATE parcel_geometry SET deleted_at=CAST(strftime('%s','now') AS INTEGER)*1000,
                updated_at=CAST(strftime('%s','now') AS INTEGER)*1000,revision=revision+1
                WHERE field_id=OLD.id AND deleted_at IS NULL;
            INSERT INTO gis_changes SELECT lower(hex(randomblob(16))),'parcel_geometry',id,
                revision,updated_at FROM parcel_geometry WHERE field_id=OLD.id;
        END;
        INSERT OR IGNORE INTO migration_flags(name) VALUES('gis_geometry_v1');
    """)
    columns = {row[1] for row in connection.execute('PRAGMA table_info(geo_tracks)')}
    if 'segment_starts_json' not in columns:
        connection.execute("ALTER TABLE geo_tracks ADD COLUMN segment_starts_json TEXT NOT NULL DEFAULT '[0]'")
    if 'state' not in columns:
        connection.execute("ALTER TABLE geo_tracks ADD COLUMN state TEXT NOT NULL DEFAULT 'stopped'")
    connection.execute("INSERT OR IGNORE INTO migration_flags(name) VALUES('gis_tracks_v2')")


POINT_TYPES = ("tree", "valve", "irrigation", "tank", "borehole", "problem", "note", "other")


class GeometryStore:
    def __init__(self, db):
        self.db = db

    @staticmethod
    def _queue(con, entity, identity, revision, now):
        con.execute("INSERT INTO gis_changes VALUES(?,?,?,?,?)",
                    (str(uuid.uuid4()), entity, identity, revision, now))

    def save(self, field_id, geometry, source="manual", source_date="", expected_revision=None):
        # Validate even callers that construct a ParcelGeometry themselves.
        geometry = normalize(geometry.original, geometry.source_crs)
        now = time.time_ns() // 1_000_000
        with self.db.connect() as con:
            con.execute("BEGIN IMMEDIATE")
            field = con.execute("SELECT name,kaek FROM fields WHERE id=?", (field_id,)).fetchone()
            if field is None:
                raise ValueError("Το αγροτεμάχιο δεν υπάρχει / Missing field")
            old = con.execute("SELECT * FROM parcel_geometry WHERE field_id=?", (field_id,)).fetchone()
            if old and expected_revision != old["revision"]:
                raise ValueError("Τα όρια άλλαξαν. Άνοιξε ξανά και επίλεξε ποια έκδοση θα κρατήσεις / Geometry conflict")
            identity = old["id"] if old else str(uuid.uuid4())
            revision = old["revision"] + 1 if old else 1
            con.execute("""INSERT INTO parcel_geometry VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
                ON CONFLICT(id) DO UPDATE SET name=excluded.name,kaek=excluded.kaek,
                original_geojson=excluded.original_geojson,source_crs=excluded.source_crs,
                wgs84_geojson=excluded.wgs84_geojson,area_m2=excluded.area_m2,
                perimeter_m=excluded.perimeter_m,centroid_lon=excluded.centroid_lon,
                centroid_lat=excluded.centroid_lat,bbox=excluded.bbox,
                geometry_source=excluded.geometry_source,geometry_source_date=excluded.geometry_source_date,
                updated_at=excluded.updated_at,deleted_at=NULL,revision=excluded.revision""",
                (identity, field_id, field["name"], field["kaek"], json.dumps(geometry.original),
                 geometry.source_crs, json.dumps(geometry.wgs84), geometry.area_m2,
                 geometry.perimeter_m, geometry.centroid_lon, geometry.centroid_lat,
                 json.dumps(geometry.bbox), source, source_date,
                 old["created_at"] if old else now, now, None, None, revision))
            self._queue(con, "parcel_geometry", identity, revision, now)
        return identity

    def get(self, field_id):
        row = self.db.query_one("""SELECT g.*,f.name AS current_name,f.kaek AS current_kaek
            FROM parcel_geometry g JOIN fields f ON g.field_id=f.id
            WHERE field_id=? AND deleted_at IS NULL""", (field_id,))
        return dict(row) if row else None

    def all(self):
        return [dict(r) for r in self.db.query("""SELECT g.*,f.name AS current_name,
            f.kaek AS current_kaek FROM parcel_geometry g JOIN fields f ON g.field_id=f.id
            WHERE deleted_at IS NULL ORDER BY f.name""")]

    def points(self, parcel_id):
        return [dict(r) for r in self.db.query(
            "SELECT * FROM geo_points WHERE parcel_id=? AND deleted_at IS NULL ORDER BY created_at,id",
            (parcel_id,))]

    def save_point(self, parcel_id, point_type, title, notes, lon, lat, accuracy, identity=None, expected_revision=None):
        import math
        check_position(lon, lat)
        if point_type not in POINT_TYPES or not title.strip() or not math.isfinite(accuracy) or accuracy < 0:
            raise ValueError("Invalid point type/title/accuracy")
        now = time.time_ns() // 1_000_000
        with self.db.connect() as con:
            con.execute("BEGIN IMMEDIATE")
            if con.execute("SELECT 1 FROM parcel_geometry WHERE id=? AND deleted_at IS NULL", (parcel_id,)).fetchone() is None:
                raise ValueError("Missing parcel")
            old = con.execute("SELECT * FROM geo_points WHERE id=? AND parcel_id=? AND deleted_at IS NULL",
                              (identity, parcel_id)).fetchone() if identity else None
            if identity and not old:
                raise ValueError("Missing point")
            if old and old['revision'] != expected_revision:
                raise ValueError('Point revision conflict')
            identity = identity or str(uuid.uuid4())
            revision = old["revision"]+1 if old else 1
            con.execute("""INSERT INTO geo_points VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?)
                ON CONFLICT(id) DO UPDATE SET point_type=excluded.point_type,title=excluded.title,
                notes=excluded.notes,longitude=excluded.longitude,latitude=excluded.latitude,
                accuracy=excluded.accuracy,updated_at=excluded.updated_at,revision=excluded.revision""",
                (identity, parcel_id, point_type, title.strip(), notes, lon, lat, accuracy,
                 old["created_at"] if old else now, now, None, None, revision))
            self._queue(con, "geo_points", identity, revision, now)
        return identity

    def delete_object(self, entity, identity, expected_revision):
        if entity not in ('geo_points', 'geo_tracks'):
            raise ValueError('Unsupported GIS object')
        now = time.time_ns() // 1_000_000
        with self.db.connect() as con:
            con.execute('BEGIN IMMEDIATE')
            count = con.execute(f'UPDATE {entity} SET deleted_at=?,updated_at=?,revision=revision+1 '
                                'WHERE id=? AND revision=? AND deleted_at IS NULL',
                                (now, now, identity, expected_revision)).rowcount
            if count != 1:
                raise ValueError('GIS revision conflict')
            self._queue(con, entity, identity, expected_revision+1, now)

    def tracks(self, parcel_id):
        return [dict(row) for row in self.db.query(
            'SELECT * FROM geo_tracks WHERE parcel_id=? AND deleted_at IS NULL ORDER BY created_at,id', (parcel_id,))]

    def save_track(self, parcel_id, payload, identity=None, expected_revision=None):
        from .tracks import validate_track
        value = validate_track(payload)
        now = time.time_ns() // 1_000_000
        with self.db.connect() as con:
            con.execute('BEGIN IMMEDIATE')
            if not con.execute('SELECT 1 FROM parcel_geometry WHERE id=? AND deleted_at IS NULL', (parcel_id,)).fetchone():
                raise ValueError('Missing parcel')
            old = con.execute('SELECT * FROM geo_tracks WHERE id=? AND parcel_id=? AND deleted_at IS NULL', (identity, parcel_id)).fetchone() if identity else None
            if identity and not old:
                raise ValueError('Missing track')
            if old and old['revision'] != expected_revision:
                raise ValueError('Track revision conflict')
            identity = identity or str(uuid.uuid4())
            revision = old['revision']+1 if old else 1
            con.execute('''INSERT INTO geo_tracks(id,parcel_id,title,positions_json,started_at,ended_at,
                duration_ms,distance_m,created_at,updated_at,deleted_at,last_sync_at,revision,segment_starts_json,state)
                VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?) ON CONFLICT(id) DO UPDATE SET
                title=excluded.title,positions_json=excluded.positions_json,started_at=excluded.started_at,
                ended_at=excluded.ended_at,duration_ms=excluded.duration_ms,distance_m=excluded.distance_m,
                updated_at=excluded.updated_at,revision=excluded.revision,
                segment_starts_json=excluded.segment_starts_json,state=excluded.state''',
                (identity,parcel_id,value['title'],json.dumps(value['positions']),value['started_at'],value['ended_at'],
                 value['duration_ms'],value['distance_m'],old['created_at'] if old else now,now,None,None,revision,
                 json.dumps(value['segment_starts']),value['state']))
            self._queue(con,'geo_tracks',identity,revision,now)
        return identity
