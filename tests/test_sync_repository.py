import copy
import sqlite3
from pathlib import Path
import tempfile
import unittest
from app.database import Database
from app.gis.geometry import normalize
from app.gis.store import GeometryStore
from app.gis.sync_repository import SQLiteSyncRepository
from app.gis.sync_contract import SyncCoordinator,fingerprint
from tests.sync_fixtures import MemoryTransport
from tests.test_sync_contract import parcel

DATASET='00000000-0000-0000-0000-000000000010'


class SQLiteSyncTests(unittest.TestCase):
    def test_storage_failure_rolls_back_metadata_geometry_and_ack_then_retry_converges(self):
        self.sync.run(self.ra,self.server);self.sync.run(self.rb,self.server)
        self.a.execute('UPDATE fields SET name=?',('Remote new name',));self.sync.run(self.ra,self.server)
        with self.b.connect() as connection:before=list(connection.iterdump())
        cursor=self.rb.cursor()
        self.b.execute("CREATE TRIGGER qa_storage_failure BEFORE UPDATE ON parcel_geometry BEGIN SELECT RAISE(ABORT,'simulated storage failure'); END")
        try:
            with self.assertRaisesRegex(sqlite3.IntegrityError,'simulated storage failure'):self.sync.run(self.rb,self.server)
            self.assertEqual(cursor,self.rb.cursor())
        finally:self.b.execute('DROP TRIGGER qa_storage_failure')
        with self.b.connect() as connection:self.assertEqual(before,list(connection.iterdump()))
        self.assertEqual(1,self.sync.run(self.rb,self.server)['pulled'])
        self.assertEqual(self.ra.documents(),self.rb.documents())
        self.assertEqual({'pulled':0,'pushed':0,'conflicts':0},self.sync.run(self.rb,self.server))
        self.assertEqual(1,len(self.b.query('SELECT * FROM fields')))

    def setUp(self):
        self.temp=tempfile.TemporaryDirectory()
        self.a=Database(Path(self.temp.name)/'a.db');self.b=Database(Path(self.temp.name)/'b.db')
        self.ra=SQLiteSyncRepository(self.a,DATASET);self.rb=SQLiteSyncRepository(self.b,DATASET)
        self.server=MemoryTransport();self.sync=SyncCoordinator()
        field=self.a.execute('INSERT INTO fields(name,kaek,notes) VALUES(?,?,?)',('Synthetic','001','Private local notes'))
        self.identity=GeometryStore(self.a).save(field,normalize(parcel()['data']['original_geometry'],'EPSG:4326'))

    def tearDown(self):self.temp.cleanup()

    def test_real_database_delta_geometry_points_tracks_and_reopen(self):
        geo=GeometryStore(self.a)
        point=geo.save_point(self.identity,'tree','Tree','',26,38,5)
        track=geo.save_track(self.identity,dict(title='Walk',positions=[[26,38,5,1000]],segment_starts=[0],
            state='stopped',started_at=1000,ended_at=1100,duration_ms=100,distance_m=0))
        self.assertEqual(3,self.sync.run(self.ra,self.server)['pushed'])
        self.assertEqual(3,self.sync.run(self.rb,self.server)['pulled'])
        self.assertEqual(self.ra.documents(),self.rb.documents())
        self.assertFalse(self.a.query('SELECT * FROM gis_changes'))
        self.rb=SQLiteSyncRepository(Database(self.b.path),DATASET)
        self.assertEqual(3,self.rb.cursor());self.assertEqual(0,self.sync.run(self.rb,self.server)['pushed'])
        self.b.execute('UPDATE fields SET kaek=?',('Android-side edit',))
        self.assertEqual(1,self.sync.run(self.rb,self.server)['pushed'])
        self.sync.run(self.ra,self.server)
        self.assertEqual('Android-side edit',self.a.query_one('SELECT kaek FROM fields')['kaek'])
        self.assertEqual('Private local notes',self.a.query_one('SELECT notes FROM fields')['notes'])
        self.assertIsNotNone(self.ra.document(point));self.assertIsNotNone(self.ra.document(track))

    def test_conflict_survives_reopen_explicit_resolution_and_stale_preview(self):
        self.sync.run(self.ra,self.server);self.sync.run(self.rb,self.server)
        self.a.execute('UPDATE fields SET name=?',('A offline',));self.b.execute('UPDATE fields SET name=?',('B offline',))
        self.sync.run(self.ra,self.server);self.sync.run(self.rb,self.server)
        self.rb=SQLiteSyncRepository(Database(self.b.path),DATASET)
        conflict=self.rb.conflicts()[0]
        self.assertEqual('B offline',conflict['local']['data']['name'])
        self.assertEqual('A offline',conflict['remote']['record']['data']['name'])
        self.b.execute('UPDATE fields SET name=?',('Later edit',))
        with self.assertRaisesRegex(ValueError,'changed'):self.rb.resolve(conflict['id'],'remote')
        self.assertTrue(self.rb.blocked(self.identity))
        self.b.execute('UPDATE fields SET name=?',('B offline',))
        self.rb.resolve(conflict['id'],'local');self.sync.run(self.rb,self.server);self.sync.run(self.ra,self.server)
        self.assertEqual('B offline',self.ra.document(self.identity)['data']['name'])
        self.assertEqual('local',self.b.query_one('SELECT resolution FROM gis_sync_conflicts')['resolution'])

    def test_atomic_apply_rejects_stale_identity_and_retains_queue_during_upload(self):
        self.sync.run(self.ra,self.server);self.sync.run(self.rb,self.server)
        current=self.ra.document(self.identity);digest=fingerprint(current)
        remote=copy.deepcopy(self.server.rows[self.identity]);remote['version']+=1;remote['record']['data']['name']='Remote'
        self.a.execute('UPDATE fields SET name=?',('Local concurrent',))
        with self.assertRaisesRegex(ValueError,'changed'):self.ra.apply(remote,digest)
        self.assertEqual('Local concurrent',self.ra.document(self.identity)['data']['name'])
        self.assertEqual(1,self.ra.state(self.identity)['remote_version'])
        g=GeometryStore(self.a);old=g.all()[0]
        g.save(old['field_id'],normalize(parcel()['data']['original_geometry'],'EPSG:4326'),expected_revision=old['revision'])
        self.ra.acknowledge(self.identity,digest,2)
        self.assertTrue(self.a.query('SELECT * FROM gis_changes'))
        self.assertNotEqual(fingerprint(self.ra.document(self.identity)),self.ra.state(self.identity)['local_hash'])

    def test_deleted_field_propagates_tombstones_without_deleting_recipient_business_data(self):
        point=GeometryStore(self.a).save_point(self.identity,'note','Keep payload','Evidence',26,38,5)
        self.sync.run(self.ra,self.server);self.sync.run(self.rb,self.server)
        self.a.execute('DELETE FROM fields')
        self.assertEqual(2,self.sync.run(self.ra,self.server)['pushed'])
        self.sync.run(self.rb,self.server)
        self.assertEqual(1,len(self.b.query('SELECT * FROM fields')))
        self.assertIsNotNone(self.rb.document(self.identity)['deleted_at'])
        self.assertIsNotNone(self.rb.document(point)['deleted_at'])
        self.assertEqual('Evidence',self.rb.document(point)['data']['notes'])
        self.assertFalse(GeometryStore(self.b).all())

    def test_dataset_state_is_separate_and_invalid_batch_cannot_advance_cursor(self):
        self.sync.run(self.ra,self.server)
        other=SQLiteSyncRepository(self.a,'00000000-0000-0000-0000-000000000011')
        self.assertIsNone(other.state(self.identity));self.assertEqual(0,other.cursor())
        self.server.rows[self.identity]['sequence']=999
        with self.assertRaises(ValueError):self.sync.run(self.rb,self.server)
        self.assertEqual(0,self.rb.cursor());self.assertFalse(self.rb.documents())

    def test_divergent_polygons_are_preserved_without_merge(self):
        self.sync.run(self.ra,self.server);self.sync.run(self.rb,self.server)
        for db,offset in ((self.a,.0001),(self.b,.0002)):
            store=GeometryStore(db);row=store.all()[0];source=copy.deepcopy(parcel()['data']['original_geometry'])
            source['coordinates'][0][1][0]+=offset
            store.save(row['field_id'],normalize(source,'EPSG:4326'),expected_revision=row['revision'])
        a=self.ra.document(self.identity)['data']['original_geometry'];b=self.rb.document(self.identity)['data']['original_geometry']
        self.assertNotEqual(a,b);self.sync.run(self.ra,self.server);self.sync.run(self.rb,self.server)
        conflict=self.rb.conflicts()[0]
        self.assertEqual(b,conflict['local']['data']['original_geometry'])
        self.assertEqual(a,conflict['remote']['record']['data']['original_geometry'])
        self.assertEqual(b,self.rb.document(self.identity)['data']['original_geometry'])
        self.rb.resolve(conflict['id'],'remote');self.assertEqual(a,self.rb.document(self.identity)['data']['original_geometry'])
        self.assertEqual(0,self.sync.run(self.rb,self.server)['pushed'])


if __name__=='__main__':unittest.main()
