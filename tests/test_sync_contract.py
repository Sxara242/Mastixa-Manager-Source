import copy
import unittest
from app.gis.sync_contract import SyncCoordinator,validate
from tests.sync_fixtures import MemoryTransport,MemoryRepository


def parcel():
    identity='00000000-0000-0000-0000-000000000001'
    return dict(schema=1,id=identity,parcel_id=identity,kind='parcel',created_at=1000,updated_at=1000,deleted_at=None,
                data=dict(name='Synthetic parcel',kaek='001',geometry_source='fixture',geometry_source_date='',source_crs='EPSG:4326',original_geometry={'type':'Polygon','coordinates':[[[26,38],[26.001,38],[26.001,38.001],[26,38.001],[26,38]]]}))


class SyncContractTests(unittest.TestCase):
    def test_both_directions_offline_conflict_resolution_and_no_echo(self):
        pc=MemoryRepository();android=MemoryRepository();server=MemoryTransport();sync=SyncCoordinator();p=parcel();identity=p['id'];pc.rows[identity]=p
        self.assertEqual(1,sync.run(pc,server)['pushed']);self.assertEqual(1,sync.run(android,server)['pulled']);self.assertEqual(pc.rows,android.rows)
        self.assertEqual(0,sync.run(android,server)['pushed']);self.assertEqual(1,server.uploads)
        android.rows[identity]['data']['name']='Android edit';sync.run(android,server);sync.run(pc,server);self.assertEqual('Android edit',pc.rows[identity]['data']['name'])
        server.offline=True;pc.rows[identity]['data']['kaek']='PC offline';android.rows[identity]['data']['kaek']='Android offline'
        with self.assertRaises(ConnectionError):sync.run(pc,server)
        server.offline=False;sync.run(pc,server);self.assertEqual(1,sync.run(android,server)['conflicts']);self.assertEqual('Android offline',android.rows[identity]['data']['kaek']);self.assertEqual('PC offline',android.conflicts[0]['remote']['record']['data']['kaek'])
        android.resolve(0,'local');sync.run(android,server);sync.run(pc,server);self.assertEqual('Android offline',pc.rows[identity]['data']['kaek']);self.assertFalse(android.conflicts)

    def test_lost_ack_retry_deduplicates_and_delete_conflict_preserves_both(self):
        repo=MemoryRepository();other=MemoryRepository();server=MemoryTransport();sync=SyncCoordinator();p=parcel();identity=p['id'];repo.rows[identity]=p;server.lose_ack=True
        with self.assertRaises(ConnectionError):sync.run(repo,server)
        sync.run(repo,server);self.assertEqual(1,server.uploads);sync.run(other,server)
        repo.rows[identity]['deleted_at']=2000;other.rows[identity]['data']['name']='Preserve me';sync.run(repo,server);sync.run(other,server)
        self.assertIsNone(other.rows[identity]['deleted_at']);self.assertEqual(2000,other.conflicts[0]['remote']['record']['deleted_at']);other.resolve(0,'remote');self.assertEqual(2000,other.rows[identity]['deleted_at'])

    def test_invalid_records_and_dependent_edit_block_parent_deletion(self):
        bad=parcel();bad['data']['source_crs']='EPSG:4979'
        with self.assertRaises(ValueError):validate(bad)
        a=MemoryRepository();b=MemoryRepository();server=MemoryTransport();sync=SyncCoordinator();p=parcel();identity=p['id'];a.rows[identity]=p;sync.run(a,server);sync.run(b,server)
        point=dict(schema=1,id='00000000-0000-0000-0000-000000000002',parcel_id=identity,kind='point',created_at=1000,updated_at=1000,deleted_at=None,data=dict(point_type='tree',title='New tree',notes='',longitude=26,latitude=38,accuracy=5))
        b.rows[point['id']]=point;a.rows[identity]['deleted_at']=2000;sync.run(a,server);result=sync.run(b,server)
        self.assertEqual(1,result['conflicts']);self.assertEqual(0,result['pushed']);self.assertIsNone(b.rows[identity]['deleted_at']);self.assertIn(point['id'],b.rows)


if __name__=='__main__':unittest.main()
