import io
import json
from pathlib import Path
import tempfile
import unittest
import zipfile

from app.database import Database
from app.gis.geometry import manual_coordinates, normalize, vertices
from app.gis.importers import import_geometry
from app.gis.store import GeometryStore


def square(x=26, y=38, size=.001):
    return [[x,y],[x+size,y],[x+size,y+size],[x,y+size],[x,y]]


class GeometryTests(unittest.TestCase):
    def test_geodesic_metrics_order_holes_and_containment(self):
        outer, hole = square(), square(26.0002,38.0002,.0002)
        original = {'type':'Polygon','coordinates':[outer,hole]}
        g = normalize(original,'EPSG:4326')
        self.assertEqual(original,g.original)
        self.assertEqual(8,g.vertex_count)
        self.assertEqual([1,2,3,4,1,2,3,4],[r[2] for r in vertices(g.original)])
        self.assertTrue(g.contains(26,38))
        self.assertFalse(g.contains(26.0003,38.0003))
        self.assertTrue(g.contains(26.0008,38.0008))
        self.assertGreater(g.area_m2,9300)
        self.assertLess(g.area_m2,9400)
        self.assertGreater(g.perimeter_m,470)

    def test_invalid_geometry_rejected_without_repair(self):
        cases=[{'type':'Polygon','coordinates':[[[0,0],[1,1],[0,1],[1,0],[0,0]]]},
               {'type':'Polygon','coordinates':[[[0,0],[1,0],[0,1]]]},
               {'type':'Point','coordinates':[26,38]},
               {'type':'Polygon','coordinates':[square(200,38)]},
               {'type':'Polygon','coordinates':[[[0,0],[1,0],[1,float('nan')],[0,0]]]}]
        for value in cases:
            with self.subTest(value=value),self.assertRaises(ValueError): normalize(value,'EPSG:4326')

    def test_manual_closure_and_original_source_retained(self):
        g=manual_coordinates('500000 4200000\n500100 4200000\n500100 4200100\n500000 4200100','EPSG:2100')
        self.assertEqual(4,g.vertex_count)
        self.assertEqual([500000,4200000],g.original['coordinates'][0][0])
        self.assertEqual('EPSG:2100',g.source_crs)
        self.assertTrue(23<g.centroid_lon<25)
        self.assertTrue(37<g.centroid_lat<39)

    def test_geojson_crs_and_multiple_features(self):
        feature={'type':'Feature','properties':{},'geometry':{'type':'Polygon','coordinates':[square()]}}
        self.assertEqual('EPSG:4326',import_geometry(json.dumps(feature).encode(),'a.geojson').source_crs)
        collection={'type':'FeatureCollection','features':[feature,feature]}
        with self.assertRaises(ValueError): import_geometry(json.dumps(collection).encode(),'a.json')
        feature['crs']={'type':'name','properties':{'name':'EPSG:2100'}}
        with self.assertRaises(ValueError): import_geometry(json.dumps(feature).encode(),'a.json','EPSG:4326')

    def test_kml_hole_and_gml_authority_axis_order(self):
        ring=' '.join(f'{x},{y},0' for x,y in square())
        kml=f'<kml xmlns="http://www.opengis.net/kml/2.2"><Placemark><Polygon><outerBoundaryIs><LinearRing><coordinates>{ring}</coordinates></LinearRing></outerBoundaryIs></Polygon></Placemark></kml>'
        g=import_geometry(kml.encode(),'a.kml')
        numbers=' '.join(f'{y} {x}' for x,y in square())
        gml=f'<gml:Polygon xmlns:gml="http://www.opengis.net/gml/3.2" srsName="urn:ogc:def:crs:EPSG::4326"><gml:exterior><gml:LinearRing><gml:posList>{numbers}</gml:posList></gml:LinearRing></gml:exterior></gml:Polygon>'
        self.assertEqual(g.original,import_geometry(gml.encode(),'a.gml').original)
        with self.assertRaises(Exception): import_geometry(b'<!DOCTYPE x [<!ENTITY a SYSTEM "file:///secret">]><x>&a;</x>','a.gml')

    def test_shapefile_zip_and_linear_dxf(self):
        import shapefile
        import ezdxf
        from pyproj import CRS
        shp,shx,dbf=io.BytesIO(),io.BytesIO(),io.BytesIO()
        with shapefile.Writer(shp=shp,shx=shx,dbf=dbf,shapeType=shapefile.POLYGON) as writer:
            writer.field('name','C');writer.poly([list(reversed(square()))]);writer.record('Synthetic')
        archive=io.BytesIO()
        with zipfile.ZipFile(archive,'w') as z:
            for ext,data in [('shp',shp.getvalue()),('shx',shx.getvalue()),('dbf',dbf.getvalue()),('prj',CRS('EPSG:4326').to_wkt().encode())]: z.writestr('field.'+ext,data)
        self.assertEqual(4,import_geometry(archive.getvalue(),'field.zip').vertex_count)
        doc=ezdxf.new();doc.modelspace().add_lwpolyline(square()[:-1],close=True)
        stream=io.StringIO();doc.write(stream)
        self.assertEqual(4,import_geometry(stream.getvalue().encode(),'field.dxf','EPSG:4326').vertex_count)

    def test_storage_atomicity_conflicts_and_field_delete_preserve_geometry(self):
        with tempfile.TemporaryDirectory() as directory:
            db=Database(Path(directory)/'test.db')
            field=db.execute('INSERT INTO fields(name,kaek) VALUES(?,?)',('Synthetic','test'))
            store=GeometryStore(db)
            g=normalize({'type':'Polygon','coordinates':[square()]},'EPSG:4326')
            identity=store.save(field,g)
            point=store.save_point(identity,'tree','Tree','',26.0005,38.0005,8)
            self.assertEqual(point,store.points(identity)[0]['id'])
            before=db.query_one('SELECT count(*) n FROM gis_changes')['n']
            with self.assertRaises(ValueError): store.save(field,g,expected_revision=99)
            with self.assertRaises(ValueError): store.save_point(identity,'tree','Tree','',999,38,5)
            self.assertEqual(before,db.query_one('SELECT count(*) n FROM gis_changes')['n'])
            self.assertEqual(identity,store.save(field,g,expected_revision=1))
            self.assertEqual(2,store.get(field)['revision'])
            db.execute('DELETE FROM fields WHERE id=?',(field,))
            row=db.query_one('SELECT * FROM parcel_geometry WHERE id=?',(identity,))
            self.assertIsNotNone(row['deleted_at']);self.assertIsNone(row['field_id'])
            self.assertEqual(1,len(store.points(identity)))
            Database(db.path) # additive migration can run repeatedly
            self.assertEqual(1,db.query_one('SELECT count(*) n FROM parcel_geometry')['n'])


if __name__=='__main__': unittest.main()
