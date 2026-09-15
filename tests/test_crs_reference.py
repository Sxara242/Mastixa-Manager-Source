import json
from pathlib import Path
import unittest
from app.gis.geometry import transformer,crs_name,manual_coordinates,vertices


class CrsReferenceTests(unittest.TestCase):
    def test_published_xy_reference_pairs_and_reverse_tolerances(self):
        cases=json.loads((Path(__file__).parents[1]/'shared/fixtures/crs_reference.json').read_text())['references']
        for case in cases:
            with self.subTest(case=case['name']):
                actual=transformer(case['source'],case['target']).transform(*case['input'],errcheck=True)
                for got,want in zip(actual,case['output']):self.assertAlmostEqual(want,got,delta=case['tolerance'])
                back=transformer(case['target'],case['source']).transform(*actual,errcheck=True)
                for got,want in zip(back,case['input']):self.assertAlmostEqual(want,got,delta=case['reverse_tolerance'])
        wrong=transformer('EPSG:4326','EPSG:3857').transform(12,15,errcheck=True)
        self.assertGreater(abs(wrong[0]-1669792.3618991035),100000)

    def test_unknown_3d_and_geocentric_rejected_original_order_retained(self):
        for name in ['EPSG:4978','EPSG:4979','EPSG:999999']:
            with self.assertRaises(Exception):crs_name(name)
        geometry=manual_coordinates('500000.12345678 4200000\n500010 4200000\n500010 4200010\n500000.12345678 4200010','EPSG:2100')
        original=list(vertices(geometry.original));self.assertEqual(4,len(original));self.assertEqual(500000.12345678,original[0][3]);self.assertEqual((1,1,1),original[0][:3])
        normalized=manual_coordinates('26 38\n26.001 38\n26.001 38.001\n26 38.001','EPSG:4326')
        self.assertEqual(normalized.original,normalized.wgs84)


if __name__=='__main__':unittest.main()
