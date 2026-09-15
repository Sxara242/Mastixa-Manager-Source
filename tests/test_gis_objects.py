import copy
import json
from pathlib import Path
import tempfile
import unittest
from pyproj import Geod
from app.database import Database
from app.gis.geometry import manual_coordinates
from app.gis.store import GeometryStore


class GeoObjectTests(unittest.TestCase):
    def test_point_conflict_track_segments_and_tombstones(self):
        with tempfile.TemporaryDirectory() as folder:
            db=Database(Path(folder)/'fixture.db');field=db.execute('INSERT INTO fields(name) VALUES(?)',('Synthetic',))
            store=GeometryStore(db);parcel=store.save(field,manual_coordinates('26 38\n26.001 38\n26.001 38.001\n26 38.001','EPSG:4326'))
            point=store.save_point(parcel,'tree','Tree','',26,38,5)
            with self.assertRaisesRegex(ValueError,'conflict'):
                store.save_point(parcel,'tree','Stale','',26,38,5,identity=point,expected_revision=0)
            self.assertEqual('Tree',store.points(parcel)[0]['title'])
            store.save_point(parcel,'valve','Valve','kept',26,38,6,identity=point,expected_revision=1)
            self.assertEqual(2,store.points(parcel)[0]['revision'])
            distance=Geod(ellps='WGS84').inv(26,38,26.001,38)[2]
            payload=dict(title='Walk',positions=[[26,38,5,1000],[26.001,38,5,6000],[27,38,5,20000]],segment_starts=[0,2],
                         started_at=1000,ended_at=21000,state='stopped',duration_ms=6000,distance_m=distance)
            track=store.save_track(parcel,payload);row=store.tracks(parcel)[0]
            self.assertEqual(payload['positions'],json.loads(row['positions_json']))
            self.assertEqual([0,2],json.loads(row['segment_starts_json']))
            self.assertAlmostEqual(distance,row['distance_m'])
            for key,bad in [('distance_m',0),('segment_starts',[0,3]),('duration_ms',-1)]:
                invalid=copy.deepcopy(payload);invalid[key]=bad
                with self.assertRaises(ValueError):store.save_track(parcel,invalid)
            self.assertEqual(1,len(store.tracks(parcel)))
            Database(db.path)
            self.assertEqual('Walk',store.tracks(parcel)[0]['title'])
            store.delete_object('geo_points',point,2);store.delete_object('geo_tracks',track,1)
            self.assertFalse(store.points(parcel));self.assertFalse(store.tracks(parcel))
            self.assertEqual(2,db.query_one('SELECT revision FROM geo_tracks WHERE id=?',(track,))['revision'])


if __name__=='__main__':unittest.main()
