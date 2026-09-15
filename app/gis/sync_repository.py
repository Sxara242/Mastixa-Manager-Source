"""Profile-local SQLite sync journal. No network or credentials are stored here."""
import json
import time
import uuid
from .geometry import normalize
from .sync_contract import canonical, fingerprint, validate


def migrate(con):
    con.executescript('''
        CREATE TABLE IF NOT EXISTS gis_sync_state(
            dataset TEXT NOT NULL,id TEXT NOT NULL,local_hash TEXT NOT NULL,
            remote_version INTEGER NOT NULL CHECK(remote_version>0),
            PRIMARY KEY(dataset,id));
        CREATE TABLE IF NOT EXISTS gis_sync_cursor(
            dataset TEXT PRIMARY KEY,position INTEGER NOT NULL CHECK(position>=0));
        CREATE TABLE IF NOT EXISTS gis_sync_conflicts(
            id TEXT PRIMARY KEY,dataset TEXT NOT NULL,entity_id TEXT NOT NULL,
            local_json TEXT NOT NULL,remote_json TEXT NOT NULL,reason TEXT NOT NULL,
            created_at INTEGER NOT NULL,resolution TEXT,
            resolved_at INTEGER);
        CREATE INDEX IF NOT EXISTS gis_sync_open_conflicts
            ON gis_sync_conflicts(dataset,entity_id,resolution);
        INSERT OR IGNORE INTO migration_flags(name) VALUES('gis_sync_v1');
    ''')


class SQLiteSyncRepository:
    def __init__(self, db, dataset):
        if str(uuid.UUID(dataset)) != dataset:
            raise ValueError('Explicit dataset UUID required')
        self.db, self.dataset = db, dataset

    def _documents(self, con):
        result = []
        parents = {}
        for row in con.execute('''SELECT g.*,f.name AS current_name,f.kaek AS current_kaek
                FROM parcel_geometry g LEFT JOIN fields f ON f.id=g.field_id'''):
            row = dict(row)
            parents[row['id']] = row
            result.append(dict(schema=1,id=row['id'],parcel_id=row['id'],kind='parcel',
                created_at=row['created_at'],updated_at=row['updated_at'],deleted_at=row['deleted_at'],
                data=dict(name=row['current_name'] if row['current_name'] is not None else row['name'],
                    kaek=row['current_kaek'] if row['current_kaek'] is not None else row['kaek'],
                    original_geometry=json.loads(row['original_geojson']),source_crs=row['source_crs'],
                    geometry_source=row['geometry_source'],geometry_source_date=row['geometry_source_date'])))
        for table,kind in (('geo_points','point'),('geo_tracks','track')):
            for row in con.execute(f'SELECT * FROM {table}'):
                row=dict(row)
                if kind=='point':
                    data={k:row[k] for k in ('point_type','title','notes','longitude','latitude','accuracy')}
                else:
                    data={k:row[k] for k in ('title','started_at','ended_at','duration_ms','distance_m','state')}
                    data.update(positions=json.loads(row['positions_json']),segment_starts=json.loads(row['segment_starts_json']))
                parent=parents[row['parcel_id']]
                # A field deletion retains children physically, but propagates tombstones.
                deleted=row['deleted_at'] if row['deleted_at'] is not None else parent['deleted_at']
                updated=max(row['updated_at'],deleted or 0)
                result.append(dict(schema=1,id=row['id'],parcel_id=row['parcel_id'],kind=kind,
                    created_at=row['created_at'],updated_at=updated,deleted_at=deleted,data=data))
        return result

    def documents(self):
        with self.db.connect() as con:
            con.execute('BEGIN')
            return self._documents(con)

    def _document(self,con,identity):
        return next((r for r in self._documents(con) if r['id']==identity),None)

    def document(self,identity):
        with self.db.connect() as con:
            con.execute('BEGIN')
            return self._document(con,identity)

    def cursor(self):
        row=self.db.query_one('SELECT position FROM gis_sync_cursor WHERE dataset=?',(self.dataset,))
        return row['position'] if row else 0

    def set_cursor(self,value):
        if type(value) is not int or value<0:raise ValueError('Invalid sync cursor')
        self.db.execute('''INSERT INTO gis_sync_cursor VALUES(?,?) ON CONFLICT(dataset)
            DO UPDATE SET position=max(position,excluded.position)''',(self.dataset,value))

    def state(self,identity):
        row=self.db.query_one('SELECT local_hash,remote_version FROM gis_sync_state WHERE dataset=? AND id=?',(self.dataset,identity))
        return dict(row) if row else None

    def _acknowledge(self,con,identity,digest,version):
        if type(version) is not int or version<1:raise ValueError('Invalid remote version')
        con.execute('''INSERT INTO gis_sync_state VALUES(?,?,?,?) ON CONFLICT(dataset,id)
            DO UPDATE SET local_hash=excluded.local_hash,remote_version=excluded.remote_version
            WHERE excluded.remote_version>=remote_version''',(self.dataset,identity,digest,version))
        now=time.time_ns()//1_000_000
        for table in ('parcel_geometry','geo_points','geo_tracks'):
            con.execute(f'UPDATE {table} SET last_sync_at=? WHERE id=?',(now,identity))
        # Only drain the queue if no newer edit was made while an upload was in flight.
        current=self._document(con,identity)
        if current is not None and fingerprint(current)==digest:
            con.execute('DELETE FROM gis_changes WHERE entity_id=?',(identity,))

    def acknowledge(self,identity,digest,version):
        with self.db.connect() as con:
            con.execute('BEGIN IMMEDIATE')
            self._acknowledge(con,identity,digest,version)

    def blocked(self,identity):
        return bool(self.db.query_one('SELECT 1 FROM gis_sync_conflicts WHERE dataset=? AND entity_id=? AND resolution IS NULL',(self.dataset,identity)))

    def dirty_dependents(self,identity):
        return any(r['id']!=identity and r['parcel_id']==identity and
            (self.state(r['id']) is None or fingerprint(r)!=self.state(r['id'])['local_hash']) for r in self.documents())

    def conflict(self,local,remote,reason):
        validate(remote['record'])
        with self.db.connect() as con:
            con.execute('BEGIN IMMEDIATE')
            args=(self.dataset,remote['record']['id'],canonical(local),canonical(remote))
            if not con.execute('''SELECT 1 FROM gis_sync_conflicts WHERE dataset=? AND entity_id=?
                    AND local_json=? AND remote_json=? AND resolution IS NULL''',args).fetchone():
                con.execute('INSERT INTO gis_sync_conflicts VALUES(?,?,?,?,?,?,?,NULL,NULL)',
                    (str(uuid.uuid4()),*args,reason,time.time_ns()//1_000_000))

    def conflicts(self):
        return [dict(id=r['id'],local=json.loads(r['local_json']),remote=json.loads(r['remote_json']),reason=r['reason'])
            for r in self.db.query('SELECT * FROM gis_sync_conflicts WHERE dataset=? AND resolution IS NULL ORDER BY created_at,id',(self.dataset,))]

    def _apply(self,con,remote,expected_hash,explicit_resolution=False):
        record=validate(remote['record']);identity=record['id'];data=record['data']
        current=self._document(con,identity)
        if (fingerprint(current) if current is not None else None)!=expected_hash:
            raise ValueError('Local record changed since sync/conflict preview')
        if current and (current['kind']!=record['kind'] or current['parcel_id']!=record['parcel_id']):
            raise ValueError('GIS identity cannot change kind or parent')
        common=dict(id=identity,created_at=record['created_at'],updated_at=record['updated_at'],
            deleted_at=record['deleted_at'])
        if record['kind']=='parcel':
            if record['deleted_at'] is not None and not explicit_resolution:
                for child in self._documents(con):
                    if child['id']==identity or child['parcel_id']!=identity:continue
                    state=con.execute('SELECT local_hash FROM gis_sync_state WHERE dataset=? AND id=?',(self.dataset,child['id'])).fetchone()
                    if state is None or state['local_hash']!=fingerprint(child):
                        raise ValueError('Dependent changed during parent deletion')
            table='parcel_geometry';geometry=normalize(data['original_geometry'],data['source_crs'])
            old=con.execute('SELECT field_id FROM parcel_geometry WHERE id=?',(identity,)).fetchone()
            field_id=old['field_id'] if old else None
            if field_id is None and record['deleted_at'] is None:
                field_id=con.execute('INSERT INTO fields(name,kaek,area_stremma) VALUES(?,?,?)',
                    (data['name'],data['kaek'],geometry.area_m2/1000)).lastrowid
            elif field_id is not None:
                con.execute('UPDATE fields SET name=?,kaek=? WHERE id=?',(data['name'],data['kaek'],field_id))
            common.update(field_id=field_id,name=data['name'],kaek=data['kaek'],
                original_geojson=canonical(geometry.original),source_crs=geometry.source_crs,
                wgs84_geojson=canonical(geometry.wgs84),area_m2=geometry.area_m2,perimeter_m=geometry.perimeter_m,
                centroid_lon=geometry.centroid_lon,centroid_lat=geometry.centroid_lat,bbox=canonical(geometry.bbox),
                geometry_source=data['geometry_source'],geometry_source_date=data['geometry_source_date'])
        else:
            parent=con.execute('SELECT deleted_at FROM parcel_geometry WHERE id=?',(record['parcel_id'],)).fetchone()
            if parent is None or (parent['deleted_at'] is not None and record['deleted_at'] is None):
                raise ValueError('Missing or deleted parent parcel')
            common['parcel_id']=record['parcel_id']
            if record['kind']=='point':
                table='geo_points';common.update({k:data[k] for k in ('point_type','title','notes','longitude','latitude','accuracy')})
            else:
                table='geo_tracks';common.update({k:data[k] for k in ('title','started_at','ended_at','duration_ms','distance_m','state')})
                common.update(positions_json=canonical(data['positions']),segment_starts_json=canonical(data['segment_starts']))
        previous=con.execute(f'SELECT revision FROM {table} WHERE id=?',(identity,)).fetchone()
        common['revision']=previous['revision']+1 if previous else 1
        columns=','.join(common);updates=','.join(f'{k}=excluded.{k}' for k in common if k!='id')
        con.execute(f'INSERT INTO {table}({columns}) VALUES({",".join("?" for _ in common)}) ON CONFLICT(id) DO UPDATE SET {updates}',tuple(common.values()))
        if record['kind']=='parcel' and record['deleted_at'] is not None:
            for child_table in ('geo_points','geo_tracks'):
                con.execute(f'''UPDATE {child_table} SET deleted_at=?,updated_at=max(updated_at,?),revision=revision+1
                    WHERE parcel_id=? AND deleted_at IS NULL''',(record['deleted_at'],record['deleted_at'],identity))
        self._acknowledge(con,identity,fingerprint(self._document(con,identity)),remote['version'])

    def apply(self,remote,expected_hash):
        with self.db.connect() as con:
            con.execute('BEGIN IMMEDIATE')
            self._apply(con,remote,expected_hash)

    def resolve(self,conflict_id,choice):
        if choice not in ('local','remote'):raise ValueError('Explicit local or remote resolution required')
        with self.db.connect() as con:
            con.execute('BEGIN IMMEDIATE')
            row=con.execute('SELECT * FROM gis_sync_conflicts WHERE id=? AND dataset=? AND resolution IS NULL',(conflict_id,self.dataset)).fetchone()
            if row is None:raise ValueError('Conflict already resolved or missing')
            local=json.loads(row['local_json']);remote=json.loads(row['remote_json']);identity=row['entity_id']
            current=self._document(con,identity)
            if current!=local:raise ValueError('Local record changed since conflict preview')
            if choice=='remote':self._apply(con,remote,fingerprint(current) if current is not None else None,True)
            else:
                if current is None:raise ValueError('No local version to retain')
                self._acknowledge(con,identity,fingerprint(remote['record']),remote['version'])
            con.execute('UPDATE gis_sync_conflicts SET resolution=?,resolved_at=? WHERE id=?',
                (choice,time.time_ns()//1_000_000,conflict_id))
