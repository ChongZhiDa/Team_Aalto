"""
Unit tests for API clients and Cache Manager.
"""

import time
import threading
import unittest
from src.api.cache_manager import SimpleCache, RateLimiter
from src.api.datamall_client import DataMallClient
from src.api.weather_client import WeatherClient
from src.api.onemap_client import OneMapClient
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

    def test_bus_load_fallback(self):
        """get_bus_load returns fallback dict when no API key is configured."""
        client = DataMallClient(api_key="")
        result = client.get_bus_load("76239", "10e")
        self.assertEqual(result["source"], "fallback")
        self.assertIsNone(result["load"])
        self.assertIn("unavailable", result["status"].lower())

    def test_bus_load_parses_valid_response(self):
        """get_bus_load correctly parses a BusArrival response with Load field."""
        client = DataMallClient(api_key="")
        # Simulate a cached live response
        mock_response = {
            "Services": [{
                "ServiceNo": "10e",
                "NextBus": {
                    "Load": "SDA",
                    "Feature": "WAB",
                    "Type": "DD",
                }
            }]
        }
        client.cache.set("v3/BusArrival_{'BusStopCode': '76239', 'ServiceNo': '10e'}", mock_response)
        result = client.get_bus_load("76239", "10e")
        self.assertEqual(result["source"], "live")
        self.assertEqual(result["load"], "SDA")
        self.assertEqual(result["status"], "Standing Only (Load: SDA)")
        self.assertTrue(result["wheelchair_accessible"])
        self.assertEqual(result["bus_type"], "DD")

    def test_onemap_autocomplete_and_geocoding(self):
        """OneMapClient autocomplete formats results with coordinates and postal labels."""
        om = OneMapClient()
        # Mocking an elastic search response
        mock_search = {
            "found": 1,
            "results": [{
                "SEARCHVAL": "TAMPINES MRT STATION",
                "BLK_NO": "20",
                "ROAD_NAME": "TAMPINES CENTRAL 1",
                "BUILDING": "TAMPINES MRT STATION",
                "ADDRESS": "20 TAMPINES CENTRAL 1 TAMPINES MRT STATION SINGAPORE 529538",
                "POSTAL": "529538",
                "LATITUDE": "1.3533",
                "LONGITUDE": "103.9452",
            }]
        }
        om.cache.set("onemap_search_Tampines_1", mock_search)
        suggestions = om.autocomplete("Tampines")
        self.assertEqual(len(suggestions), 1)
        self.assertEqual(suggestions[0]["search_val"], "TAMPINES MRT STATION")
        self.assertEqual(suggestions[0]["postal"], "529538")
        self.assertAlmostEqual(suggestions[0]["latitude"], 1.3533)
        self.assertAlmostEqual(suggestions[0]["longitude"], 103.9452)
        self.assertIn("S529538", suggestions[0]["label"])

    def test_onemap_route_fallback(self):
        """OneMapClient get_route provides structured fallback estimates when token is not present."""
        om = OneMapClient(token="")
        route = om.get_route([1.3533, 103.9452], [1.2844, 103.8510], route_type="walk")
        self.assertEqual(route["status"], "ok")
        self.assertEqual(route["source"], "fallback_model")
        self.assertGreater(route["total_distance_m"], 0)
        self.assertGreater(route["total_duration_min"], 0)

    def test_cache_thread_safety(self):
        """SimpleCache supports concurrent multi-threaded reads and writes without error."""
        cache = SimpleCache(default_ttl_seconds=10, max_size=100)
        threads = []
        errors = []

        def worker(thread_id: int):
            try:
                for i in range(50):
                    cache.set(f"key_{thread_id}_{i}", f"val_{i}")
                    val = cache.get(f"key_{thread_id}_{i}")
                    if val != f"val_{i}":
                        errors.append(f"Mismatch in thread {thread_id}: {val}")
            except Exception as e:
                errors.append(str(e))

        for tid in range(8):
            t = threading.Thread(target=worker, args=(tid,))
            threads.append(t)
            t.start()

        for t in threads:
            t.join()

        self.assertEqual(len(errors), 0, f"Thread errors: {errors}")

    def test_cache_custom_ttl_and_eviction(self):
        """SimpleCache respects individual item TTL and enforces max capacity bounds."""
        cache = SimpleCache(default_ttl_seconds=60, max_size=5)

        # Set item with very short TTL
        cache.set("short_lived", "data", ttl=0.01)
        time.sleep(0.03)
        self.assertIsNone(cache.get("short_lived"))

        # Test capacity bounds
        for i in range(10):
            cache.set(f"k_{i}", f"v_{i}")

        # Size must never exceed max_size (5)
        self.assertLessEqual(cache.size(), 5)

    def test_rate_limiter(self):
        """RateLimiter permits up to capacity and throttles exceeding requests."""
        limiter = RateLimiter(max_calls=3, period_seconds=10.0)
        self.assertTrue(limiter.acquire(blocking=False))
        self.assertTrue(limiter.acquire(blocking=False))
        self.assertTrue(limiter.acquire(blocking=False))
        # 4th immediate call should be throttled
        self.assertFalse(limiter.acquire(blocking=False))

    def test_datamall_bundle_concurrent(self):
        """DataMallClient get_live_commute_bundle retrieves alerts, crowd, and bus concurrently."""
        client = DataMallClient(api_key="")
        bundle = client.get_live_commute_bundle(train_line="EWL", bus_stop_code="76239", bus_service_no="10e")
        self.assertIn("alerts", bundle)
        self.assertIn("pcd", bundle)
        self.assertIn("bus_load", bundle)
        self.assertEqual(bundle["alerts"]["Status"], 1)


if __name__ == "__main__":
    unittest.main()



