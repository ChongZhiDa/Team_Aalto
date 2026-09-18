"""
Unit tests for API clients and Cache Manager.
"""

import unittest
from src.api.cache_manager import SimpleCache
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


if __name__ == "__main__":
    unittest.main()


