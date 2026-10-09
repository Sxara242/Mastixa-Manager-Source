"""Qualify the named provenance changes and unchanged native PROJ selection."""
import hashlib
import json
from contextlib import closing
from pathlib import Path
import runpy
import shutil
import sqlite3
import subprocess
import sys
import tempfile
import unittest

from pyproj import datadir

ROOT = Path(__file__).resolve().parents[1]
OVERLAY = runpy.run_path(str(ROOT / "packaging/epsg_provenance.py"))
SOURCE = Path(datadir.get_data_dir()) / "proj.db"
LOCK = OVERLAY["policy"](ROOT)

# Separate processes prevent PROJ authority-factory caches hiding a database change.
PROBE = r'''
import sys,json,warnings
from pyproj import CRS,Transformer,datadir,network
from pyproj.crs import CoordinateOperation
from pyproj.transformer import TransformerGroup
from pyproj.aoi import AreaOfInterest
datadir.set_data_dir(sys.argv[1]);network.set_network_enabled(False)
result={"operations":{},"ranking":{}}
for code in [1312,1462,7001]:
 op=CoordinateOperation.from_epsg(code)
 result["operations"][str(code)]={"json":op.to_json_dict(),"wkt":op.to_wkt()}
alias=CRS.from_user_input(sys.argv[2]);official=CRS.from_epsg(3857)
result["alias"]={"json":alias.to_json_dict(),"wkt":alias.to_wkt(),"equal3857":alias.equals(official),
 "xy":Transformer.from_crs(4326,alias,always_xy=True,allow_ballpark=False).transform(24.1,38.2)}
from app.gis.geometry import crs_name,transformer
result["legacy_application"]={"crs":crs_name("EPSG:900913"),
 "xy":transformer("EPSG:900913","EPSG:4326").transform(1e6,4e6)}
try: CRS.from_epsg(900913);result["epsg900913_lookup"]=True
except Exception: result["epsg900913_lookup"]=False
for name,source,target,aoi in [
 ("canada",4267,4269,[-110,45,-100,55]),("quebec",4267,4269,[-75,45,-65,55]),
 ("netherlands",4258,5709,[4,51,6,53]),("greece",4326,2100,[23,37,26,39])]:
 with warnings.catch_warnings():
  warnings.simplefilter("ignore")
  group=TransformerGroup(source,target,always_xy=True,allow_ballpark=False,area_of_interest=AreaOfInterest(*aoi))
 result["ranking"][name]={"best_available":group.best_available,
  "available":[{"description":t.description,"accuracy":t.accuracy,"definition":t.definition} for t in group.transformers],
  "unavailable":[{"name":o.name,"accuracy":o.accuracy,"grids":[g.short_name for g in o.grids]} for o in group.unavailable_operations]}
print(json.dumps(result,sort_keys=True))
'''


def probe(directory, alias):
    completed = subprocess.run([sys.executable, "-c", PROBE, str(directory), alias],
                               capture_output=True, text=True, check=True)
    return json.loads(completed.stdout)


class WindowsEpsgProvenanceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temp = tempfile.TemporaryDirectory()
        cls.directory = Path(cls.temp.name)
        cls.derived = OVERLAY["prepare"](SOURCE, cls.directory / "derived/proj.db", ROOT)
        cls.original = probe(SOURCE.parent, "EPSG:900913")
        cls.marked = probe(cls.derived.parent, "PROJ:900913")

    @classmethod
    def tearDownClass(cls):
        cls.temp.cleanup()

    def test_supplier_immutable_and_output_deterministic(self):
        self.assertEqual(LOCK["input_sha256"], OVERLAY["digest"](SOURCE))
        second = OVERLAY["prepare"](SOURCE, self.directory / "repeat/proj.db", ROOT)
        self.assertEqual(LOCK["output_sha256"], OVERLAY["digest"](second))
        self.assertEqual(self.derived.read_bytes(), second.read_bytes())

    def test_accuracy_fields_disattributed_inside_both_direct_exports(self):
        for code in ("1312", "1462"):
            with self.subTest(code=code):
                before = self.original["operations"][code]["json"]
                after = self.marked["operations"][code]["json"]
                self.assertEqual("2.0", str(after["accuracy"]))
                self.assertEqual({"authority": "EPSG", "code": int(code)}, after["id"])
                self.assertIn(LOCK["operation_notes"][code], after["remarks"])
                self.assertIn(LOCK["operation_notes"][code], self.marked["operations"][code]["wkt"])
                self.assertEqual({k: v for k, v in before.items() if k != "remarks"},
                                 {k: v for k, v in after.items() if k != "remarks"})
                self.assertTrue(after["remarks"].startswith(before["remarks"] + " "))

    def test_interpolation_association_marked_without_changing_context(self):
        before = self.original["operations"]["7001"]["json"]
        after = self.marked["operations"]["7001"]["json"]
        self.assertIn(LOCK["operation_notes"]["7001"], after["remarks"])
        self.assertIn(LOCK["operation_notes"]["7001"], self.marked["operations"]["7001"]["wkt"])
        self.assertEqual({k: v for k, v in before.items() if k != "remarks"},
                         {k: v for k, v in after.items() if k != "remarks"})
        self.assertEqual({"authority": "EPSG", "code": 4289}, after["interpolation_crs"]["id"])

    def test_alias_is_proj_attributed_and_coordinate_equivalent(self):
        alias = self.marked["alias"]
        self.assertEqual({"authority": "PROJ", "code": 900913}, alias["json"]["id"])
        self.assertIn("unofficial", alias["json"]["name"])
        self.assertIn('ID["PROJ",900913]', alias["wkt"])
        self.assertFalse(self.marked["epsg900913_lookup"])
        self.assertTrue(alias["equal3857"])
        self.assertEqual(self.original["alias"]["xy"], alias["xy"])

    def test_internal_operation_selection_identical_in_four_scoped_areas(self):
        self.assertEqual(self.original["ranking"], self.marked["ranking"])
        self.assertTrue(self.marked["ranking"]["greece"]["available"])

    def test_only_named_storage_fields_changed(self):
        with closing(sqlite3.connect(SOURCE)) as original, closing(sqlite3.connect(self.derived)) as derived:
            for code in (1312, 1462, 7001):
                columns = [r[1] for r in original.execute("PRAGMA table_info(grid_transformation)")]
                query = "SELECT * FROM grid_transformation WHERE auth_name='EPSG' AND code=?"
                before = dict(zip(columns, original.execute(query, (code,)).fetchone()))
                after = dict(zip(columns, derived.execute(query, (code,)).fetchone()))
                self.assertEqual(["description"], [k for k in columns if before[k] != after[k]])
            columns = [r[1] for r in original.execute("PRAGMA table_info(projected_crs)")]
            before = dict(zip(columns, original.execute("SELECT * FROM projected_crs WHERE auth_name='EPSG' AND code=900913").fetchone()))
            after = dict(zip(columns, derived.execute("SELECT * FROM projected_crs WHERE auth_name='PROJ' AND code=900913").fetchone()))
            self.assertEqual(["auth_name", "name", "description"], [k for k in columns if before[k] != after[k]])
            self.assertEqual(before["deprecated"], after["deprecated"])
            self.assertEqual(("ok",), derived.execute("PRAGMA quick_check").fetchone())

    def test_legacy_application_input_canonicalized_to_genuine_epsg(self):
        from app.gis.geometry import canonical_crs_input, crs_name, transformer
        for value in ("900913", "EPSG:900913", "PROJ:900913", "urn:ogc:def:crs:EPSG::900913",
                      "http://www.opengis.net/def/crs/EPSG/0/900913"):
            with self.subTest(value=value):
                self.assertEqual("EPSG:3857", canonical_crs_input(value))
                self.assertEqual("EPSG:3857", crs_name(value))
                self.assertEqual(transformer("EPSG:3857", "EPSG:4326").transform(1e6, 4e6),
                                 transformer(value, "EPSG:4326").transform(1e6, 4e6))
        self.assertEqual("EPSG:2100", canonical_crs_input("EPSG:2100"))
        self.assertEqual(self.original["legacy_application"], self.marked["legacy_application"])
        self.assertEqual("EPSG:3857", self.marked["legacy_application"]["crs"])

    def test_unknown_supplier_or_existing_work_not_overwritten(self):
        bad = self.directory / "bad/proj.db"
        bad.parent.mkdir(exist_ok=True)
        bad.write_bytes(b"unknown")
        with self.assertRaisesRegex(ValueError, "unknown/changed supplier"):
            OVERLAY["prepare"](bad, self.directory / "unknown/proj.db", ROOT)
        output = self.directory / "existing/proj.db"
        output.parent.mkdir(exist_ok=True)
        output.write_bytes(b"preserve work")
        with self.assertRaisesRegex(ValueError, "unknown existing"):
            OVERLAY["prepare"](SOURCE, output, ROOT)
        self.assertEqual(b"preserve work", output.read_bytes())
        with self.assertRaisesRegex(ValueError, "immutable supplier"):
            OVERLAY["prepare"](SOURCE, SOURCE, ROOT)

    def test_analysis_rejects_duplicate_missing_or_relocated_database(self):
        entry = (OVERLAY["DB_DESTINATION"], str(SOURCE), "DATA")
        for entries in ([], [entry, entry], [("other/proj.db", str(SOURCE), "DATA")]):
            with self.assertRaisesRegex(ValueError, "missing, duplicate or relocated"):
                OVERLAY["normalize_analysis"](entries, ROOT, self.directory / "analysis")
        result = OVERLAY["normalize_analysis"]([entry, ("unchanged.txt", "input", "DATA")], ROOT,
                                             self.directory / "analysis")
        self.assertEqual(entry[0], result[0][0])
        self.assertEqual(LOCK["output_sha256"], OVERLAY["digest"](result[0][1]))
        self.assertEqual(("unchanged.txt", "input", "DATA"), result[1])

    def test_bundle_rejects_original_and_extra_database(self):
        bundle = self.directory / "bundle"
        target = bundle / "_internal" / OVERLAY["DB_DESTINATION"]
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(SOURCE, target)
        self.assertTrue(OVERLAY["bundle_errors"](bundle, ROOT))
        shutil.copyfile(self.derived, target)
        self.assertEqual([], OVERLAY["bundle_errors"](bundle, ROOT))
        shutil.copyfile(self.derived, bundle / "proj.db")
        self.assertTrue(OVERLAY["bundle_errors"](bundle, ROOT))


if __name__ == "__main__":
    unittest.main()
