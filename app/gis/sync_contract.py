"""Version 1 GIS wire contract. Derived geometry is recomputed by each client."""
import copy
import hashlib
import json
import uuid
from .geometry import normalize,check_position
from .store import POINT_TYPES
from .tracks import validate_track


def canonical(value):
    return json.dumps(value,sort_keys=True,separators=(',',':'),ensure_ascii=False,allow_nan=False)


def fingerprint(value):return hashlib.sha256(canonical(value).encode('utf-8')).hexdigest()


def validate(record):
    value=copy.deepcopy(record)
    if len(canonical(value).encode('utf-8'))>4*1024*1024:raise ValueError('Sync record exceeds 4 MB')
    if not isinstance(value,dict) or type(value.get('schema')) is not int or value['schema']!=1:raise ValueError('Unknown GIS sync schema')
    for key in ('id','parcel_id'):
        if str(uuid.UUID(value[key]))!=value[key]:raise ValueError('Canonical UUID required')
    for key in ('created_at','updated_at'):
        if type(value.get(key)) is not int or value[key]<0:raise ValueError('Invalid record timestamp')
    if value.get('deleted_at') is not None and (type(value['deleted_at']) is not int or value['deleted_at']<0):raise ValueError('Invalid deletion timestamp')
    data=value['data'];kind=value['kind']
    if kind=='parcel':
        if value['id']!=value['parcel_id']:raise ValueError('Parcel identity mismatch')
        for key in ('name','kaek','geometry_source','geometry_source_date'):
            if not isinstance(data.get(key),str):raise ValueError('Invalid parcel metadata')
        if not data['name'].strip():raise ValueError('Parcel name required')
        normalize(data['original_geometry'],data['source_crs'])
    elif kind=='point':
        import math
        if data.get('point_type') not in POINT_TYPES or not isinstance(data.get('title'),str) or not data['title'].strip() or not isinstance(data.get('notes'),str):raise ValueError('Invalid point')
        check_position(data['longitude'],data['latitude'])
        if isinstance(data['accuracy'],bool) or not math.isfinite(data['accuracy']) or data['accuracy']<0:raise ValueError('Invalid point accuracy')
    elif kind=='track':validate_track(data)
    else:raise ValueError('Unknown GIS sync kind')
    return value


class RemoteConflict(Exception):
    def __init__(self,remote):super().__init__('Remote record changed');self.remote=remote


def validate_remote(remote):
    if not isinstance(remote,dict):raise ValueError('Invalid remote envelope')
    for key in ('version','sequence'):
        if type(remote.get(key)) is not int or remote[key]<1:raise ValueError('Invalid remote version/sequence')
    validate(remote['record'])
    return remote


class SyncCoordinator:
    """Transport is injected; repository operations must commit data/state atomically.

    Pull first, journal conflicts durably, then push only changed records using CAS.
    A failed/uncertain upload is retried with identical content and base version.
    """
    def run(self,repository,transport):
        result={'pulled':0,'pushed':0,'conflicts':0}
        cursor,remote_rows=transport.pull(repository.cursor())
        if type(cursor) is not int or cursor<repository.cursor():raise ValueError('Invalid remote cursor')
        for remote in remote_rows:
            validate_remote(remote)
            if remote['sequence']>cursor:raise ValueError('Remote sequence exceeds cursor')
        for remote in sorted(remote_rows,key=lambda r:(r['record']['kind']!='parcel',r['sequence'])):
            incoming=validate(remote['record']);identity=incoming['id'];state=repository.state(identity)
            if state and remote['version']<=state['remote_version']:continue
            current=repository.document(identity);current_hash=fingerprint(current) if current else None
            if current==incoming:
                repository.acknowledge(identity,current_hash,remote['version']);continue
            dirty=current is not None and (state is None or current_hash!=state['local_hash'])
            dependents=incoming['kind']=='parcel' and incoming['deleted_at'] is not None and repository.dirty_dependents(identity)
            if dirty or dependents or repository.blocked(identity):
                repository.conflict(current,remote,'concurrent edit or deletion');result['conflicts']+=1
            else:
                try:repository.apply(remote,current_hash);result['pulled']+=1
                except ValueError as error:repository.conflict(repository.document(identity),remote,str(error));result['conflicts']+=1
        repository.set_cursor(cursor)
        for current in sorted(repository.documents(),key=lambda r:(r['kind']!='parcel',r['created_at'],r['id'])):
            identity=current['id'];state=repository.state(identity);digest=fingerprint(current)
            if state and digest==state['local_hash']:continue
            if repository.blocked(identity) or repository.blocked(current['parcel_id']):continue
            try:
                remote=transport.push(validate(current),state['remote_version'] if state else 0)
                validate_remote(remote)
                if remote['record']!=current:raise ValueError('Upload acknowledged different content')
                repository.acknowledge(identity,digest,remote['version']);result['pushed']+=1
            except RemoteConflict as error:
                validate_remote(error.remote)
                repository.conflict(current,error.remote,'remote compare-and-swap conflict');result['conflicts']+=1
        return result
