"""Unit tests for Wi-Fi Radar."""

import unittest
from wifi_radar.cli import get_wifi_info


class TestWifiRadar(unittest.TestCase):

    def test_get_wifi_info(self):
        info = get_wifi_info()
        self.assertIsInstance(info, dict)
        self.assertIn("interface", info)
        self.assertIn("ssid", info)


if __name__ == "__main__":
    unittest.main()
