"""Explicit emulator exchange verification; all databases are synthetic temporary files.

prepare ANDROID_RETURN WINDOWS_RETURN: import Android edits, make Desktop edits.
verify WINDOWS_RETURN ANDROID_FINAL: verify convergence and CRS invariants.
Run the corresponding GisSyncTest methods before/after prepare; see sync QA docs.
"""
import copy
import json
from pathlib import Path
import tempfile
from app.database import Database
from app.gis.geometry import normalize,vertices
from app.gis.store import GeometryStore
from app.gis.sync_contract import SyncCoordinator,validate,fingerprint
from app.gis.sync_repository import SQLiteSyncRepository
from tests.sync_fixtures import MemoryTransport

DATASET='00000000-0000-0000-0000-000000000010'
FIXTURE=Path(__file__).resolve().parents[1]/'shared/fixtures/gis_sync_exchange.json'


def sorted_records(value):
    rows=sorted(value['records'],key=lambda r:r['id'])
    assert len(rows)==3 and len({r['id'] for r in rows})==3
    for row in rows:validate(row)
    assert {r['kind'] for r in rows}=={'parcel','point','track'}
    return rows


def compare_wgs84(a,b):
    left=list(vertices(a));right=list(vertices(b))
    assert len(left)==len(right)
    maximum=0
    for x,y in zip(left,right):
        assert x[:3]==y[:3]
        maximum=max(maximum,abs(x[3]-y[3]),abs(x[4]-y[4]))
    assert maximum<=2e-7,maximum
    return maximum


def prepare(android_path,windows_path):
    android=json.loads(Path(android_path).read_text(encoding='utf-8'));initial=json.loads(FIXTURE.read_text(encoding='utf-8'))
    received=sorted_records(android);originals=sorted_records(initial)
    parcel=next(r for r in received if r['kind']=='parcel');point=next(r for r in received if r['kind']=='point');track=next(r for r in received if r['kind']=='track')
    assert parcel['data']==next(r for r in originals if r['kind']=='parcel')['data']
    assert point['data']['title']=='Αλλαγή Android' and point['data']['point_type']=='valve'
    assert all(r['deleted_at'] is None for r in received)
    error=compare_wgs84(normalize(parcel['data']['original_geometry'],parcel['data']['source_crs']).wgs84,android['wgs84'])
    with tempfile.TemporaryDirectory(prefix='mastixa-sync-exchange-') as folder:
        db=Database(Path(folder)/'synthetic.db');repo=SQLiteSyncRepository(db,DATASET);sync=SyncCoordinator();server=MemoryTransport()
        for index,row in enumerate(originals,1):repo.apply(dict(record=row,version=1,sequence=index),None)
        server.sequence=3
        server.rows={r['id']:dict(record=r,version=2,sequence=i) for i,r in enumerate(received,1)}
        sync.run(repo,server);assert sorted(repo.documents(),key=lambda r:r['id'])==received
        assert sync.run(repo,server)['pushed']==0 and server.uploads==0
        geo=GeometryStore(db);stored=geo.all()[0];source=copy.deepcopy(parcel['data']['original_geometry'])
        source['coordinates'][0][1][0]+=.25
        geo.save(stored['field_id'],normalize(source,'EPSG:2100'),source='Desktop round-trip edit',expected_revision=stored['revision'])
        geo.delete_object('geo_points',point['id'],db.query_one('SELECT revision FROM geo_points WHERE id=?',(point['id'],))['revision'])
        updated=copy.deepcopy(track['data']);updated['title']='Διαδρομή μετά από αλλαγή Windows'
        geo.save_track(parcel['id'],updated,identity=track['id'],expected_revision=db.query_one('SELECT revision FROM geo_tracks WHERE id=?',(track['id'],))['revision'])
        assert sync.run(repo,server)['pushed']==3
        assert sync.run(repo,server)['pushed']==0 and server.uploads==3
        final=repo.documents();assert len(final)==3 and not repo.conflicts()
        geometry=normalize(next(r for r in final if r['kind']=='parcel')['data']['original_geometry'],'EPSG:2100')
        output=dict(records=final,wgs84=geometry.wgs84)
        Path(windows_path).write_text(json.dumps(output,ensure_ascii=False,indent=2),encoding='utf-8')
    return dict(status='Desktop return prepared and verified',records=3,android_to_desktop_wgs84_max_degrees=error,duplicate_uploads=0)


def verify(windows_path,android_path):
    windows=json.loads(Path(windows_path).read_text(encoding='utf-8'));android=json.loads(Path(android_path).read_text(encoding='utf-8'))
    expected=sorted_records(windows);actual=sorted_records(android);assert expected==actual,'Final wire state differs'
    parcel=next(r for r in actual if r['kind']=='parcel');point=next(r for r in actual if r['kind']=='point');track=next(r for r in actual if r['kind']=='track')
    assert parcel['deleted_at'] is None and point['deleted_at'] is not None and track['deleted_at'] is None
    assert parcel['data']['source_crs']=='EPSG:2100' and parcel['data']['geometry_source']=='Desktop round-trip edit'
    assert track['data']['title']=='Διαδρομή μετά από αλλαγή Windows'
    error=compare_wgs84(windows['wgs84'],android['wgs84'])
    return dict(status='PASS actual Python -> Android -> Python -> Android exchange',records=3,
                wire_state_sha256=fingerprint(actual),wgs84_max_degrees=error,source_coordinates_exact=True,null_and_deletion_preserved=True)


if __name__=='__main__':
    import argparse
    parser=argparse.ArgumentParser();parser.add_argument('operation',choices=['prepare','verify']);parser.add_argument('first');parser.add_argument('second');args=parser.parse_args()
    print(json.dumps((prepare if args.operation=='prepare' else verify)(args.first,args.second),ensure_ascii=False,indent=2))
