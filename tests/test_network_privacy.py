import os
import subprocess
import sys
import unittest

class NetworkPrivacyTests(unittest.TestCase):
    def test_geometry_disables_environment_enabled_proj_downloads(self):
        script = "from app.gis.geometry import transformer; from pyproj import network; t=transformer('EPSG:4326','EPSG:3857'); assert not network.is_network_enabled(); assert not t.is_network_enabled; print('local-only')"
        result = subprocess.run([sys.executable, "-c", script], env={**os.environ, "PROJ_NETWORK": "ON"}, capture_output=True, text=True, timeout=30)
        self.assertEqual(0, result.returncode, result.stderr)
        self.assertIn("local-only", result.stdout)
