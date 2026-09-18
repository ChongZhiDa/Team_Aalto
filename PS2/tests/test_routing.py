"""
Unit tests for Routing & Geospatial Module.
"""

import unittest
from src.routing.coordinates import (
    EWL_STATIONS,
    DTL_STATIONS,
    get_ewl_polyline,
    get_dtl_polyline,
    ORIGIN_POINT,
    DESTINATION_POINT,
)
from src.routing.door_to_door import get_walking_legs
from src.routing.multimodal_router import MultimodalRouter


class TestRoutingModule(unittest.TestCase):
    def setUp(self):
        self.router = MultimodalRouter()

    def test_station_counts_and_polylines(self):
        self.assertEqual(len(EWL_STATIONS), 13)
        self.assertEqual(len(DTL_STATIONS), 15)
        self.assertEqual(len(get_ewl_polyline()), 13)
        self.assertEqual(len(get_dtl_polyline()), 15)

    def test_walking_legs(self):
        legs = get_walking_legs()
        self.assertIn("home_to_tampines_ewl", legs)
        self.assertIn("telok_ayer_dtl_to_desk", legs)
        self.assertGreater(legs["home_to_tampines_ewl"]["sheltered_percent"], 50)

    def test_multimodal_ewl_normal(self):
        journey = self.router.compute_ewl_journey(delay_minutes=0, crowd_level="m", disrupted_stations=[])
        self.assertEqual(journey["total_duration_min"], 42)
        self.assertEqual(journey["estimated_arrival"], "08:22 AM")
        self.assertTrue(journey["is_recommended"])

    def test_multimodal_ewl_delayed(self):
        journey = self.router.compute_ewl_journey(delay_minutes=25, crowd_level="h", disrupted_stations=["EW6"])
        self.assertEqual(journey["total_duration_min"], 67)
        self.assertEqual(journey["estimated_arrival"], "08:47 AM")
        self.assertFalse(journey["is_recommended"])

    def test_multimodal_dtl_bypass(self):
        dtl = self.router.compute_dtl_bypass(crowd_level="l", is_active_bypass=True)
        self.assertEqual(dtl["total_duration_min"], 44)
        self.assertEqual(dtl["estimated_arrival"], "08:24 AM")
        self.assertTrue(dtl["is_recommended"])


if __name__ == "__main__":
    unittest.main()

