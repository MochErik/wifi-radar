import unittest
from wifi_radar.cli import scan_wifi

class TestWifiRadar(unittest.TestCase):
    def test_scan(self):
        ok, _ = scan_wifi()
        self.assertTrue(ok)
if __name__ == "__main__": unittest.main()
