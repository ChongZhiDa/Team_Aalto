"""
Unit tests for API clients and Cache Manager.
"""

import unittest
from src.api.cache_manager import SimpleCache
from src.api.datamall_client import DataMallClient
from src.api.weather_client import WeatherClient
from src.canonical_lines import normalize_alert_line, normalize_pcd_line


class TestAPIModule(unittest.TestCase):
    def test_cache_expiration(self):
        cache = SimpleCache(default_ttl_seconds=1)
        cache.set("key1", "val1")
        self.assertEqual(cache.get("key1"), "val1")
        # Ensure clear works
        cache.clear()
        self.assertIsNone(cache.get("key1"))

    def test_datamall_fallback(self):
        # Without key, should return safe fallback dictionary
        client = DataMallClient(api_key="")
        alerts = client.get_train_service_alerts()
        self.assertEqual(alerts["Status"], 1)
        self.assertEqual(len(alerts["AffectedSegments"]), 0)

    def test_weather_defaults(self):
        client = WeatherClient()
        weather = client.get_commute_weather()
        self.assertIn("origin_forecast", weather)
        self.assertIn("rain_alert", weather)

    def test_canonical_lines(self):
        self.assertEqual(normalize_alert_line("STL"), "SKL")
        self.assertEqual(normalize_pcd_line("PLRT"), "PGL")


if __name__ == "__main__":
    unittest.main()

