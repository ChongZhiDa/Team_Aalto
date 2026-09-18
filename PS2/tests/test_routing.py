"""
Unit and Acceptance tests for Routing & Geospatial Module (Teammate 2).
Verifies:
- Issue 1: Parsing AmendmenttoMP2014RailStation.geojson for centroids and GRND_LEVEL
- Issue 2: Arbitrary station graph pathfinder across Singapore MRT
- Issue 3: Interchange platform transfer penalties (3-5 min)
- Issue 4: Dynamic rain penalties for unsheltered pedestrian paths
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
from src.routing.geojson_loader import load_geojson_stations, get_station_metadata
from src.routing.door_to_door import get_walking_legs, compute_walking_summary
from src.routing.multimodal_router import MultimodalRouter
from src.routing.graph_router import StationGraphRouter, get_transfer_penalty


class TestRoutingModule(unittest.TestCase):
    def setUp(self):
        self.router = MultimodalRouter()
        self.graph_router = StationGraphRouter()

    # --- Baseline Corridor & Polyline Tests ---
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

    # --- Teammate 2 Issue 1: GeoJSON Centroids & Ground Level ---
    def test_tc_rot_01_geojson_centroids_and_underground(self):
        """TC-ROT-01: Verifies parsing official GeoJSON for station centroids and GRND_LEVEL."""
        stations = load_geojson_stations()
        self.assertGreater(len(stations), 100, "Should load over 100 official rail stations from GeoJSON.")
        
        # Test Raffles Place attributes
        raffles = get_station_metadata("Raffles Place")
        self.assertIsNotNone(raffles)
        self.assertEqual(raffles["grnd_level"], "UNDERGROUND")
        self.assertAlmostEqual(raffles["coords"][0], 1.2834, places=2)
        self.assertAlmostEqual(raffles["coords"][1], 103.8513, places=2)

        # Test Jurong East attributes
        jurong = get_station_metadata("Jurong East")
        self.assertIsNotNone(jurong)
        self.assertEqual(jurong["grnd_level"], "ABOVEGROUND")

    # --- Teammate 2 Issue 2: Arbitrary Station Routing ---
    def test_tc_rot_02_arbitrary_station_pathfinder(self):
        """TC-ROT-02: Graph pathfinder computes journeys between arbitrary stations in Singapore."""
        # Test Jurong East to Bishan
        path = self.graph_router.find_path("Jurong East", "Bishan")
        self.assertIsNotNone(path)
        self.assertGreater(path["hops"], 0)
        self.assertIn("total_train_min", path)
        self.assertGreater(path["total_train_min"], 15)

        # Test arbitrary route through MultimodalRouter
        route = self.router.route_arbitrary_commute("Jurong East", "Bishan")
        self.assertIsNotNone(route)
        self.assertIn("legs", route)
        self.assertEqual(route["transit_type"], "Train (MRT)")

    # --- Teammate 2 Issue 3: Interchange Platform Transfer Penalties ---
    def test_tc_rot_03_transfer_penalty(self):
        """TC-ROT-03: Switching MRT lines at interchange stations incurs realistic 3-5 min walk penalty."""
        # Bugis deep underground transfer between EWL and DTL
        transfer_penalty = self.router.get_interchange_penalty(
            from_line="EWL", to_line="DTL", station="Bugis"
        )
        self.assertGreaterEqual(transfer_penalty, 3, "Interchange walk at Bugis must take at least 3 minutes.")

        # Outram Park deep interchange
        outram_penalty = get_transfer_penalty("EWL", "TEL", "Outram Park")
        self.assertEqual(outram_penalty, 5, "Deep multi-level transfer at Outram Park should be 5 minutes.")

        # City Hall cross-platform transfer
        cityhall_penalty = get_transfer_penalty("EWL", "NSL", "City Hall")
        self.assertEqual(cityhall_penalty, 2, "Cross-platform transfer at City Hall is fast (2 minutes).")

    # --- Teammate 2 Issue 4: Dynamic Rain Penalties ---
    def test_tc_rot_04_rain_shelter_penalty(self):
        """TC-ROT-04: Rain dynamically penalizes unsheltered paths while covered linkways remain unaffected."""
        dry_summary = self.router.compute_walking_summary(rain_active=False)
        wet_summary = self.router.compute_walking_summary(rain_active=True)

        # Unsheltered walking legs must be penalized when raining
        self.assertGreater(wet_summary["total_walk_min"], dry_summary["total_walk_min"])
        self.assertGreater(wet_summary["rain_delay_min"], 0)

        # EWL journey in rain should reflect rain delay
        ewl_wet = self.router.compute_ewl_journey(delay_minutes=0, crowd_level="m", disrupted_stations=[], rain_active=True)
        self.assertGreaterEqual(ewl_wet["total_duration_min"], 43)
        self.assertIn("Rain", ewl_wet["status"])


if __name__ == "__main__":
    unittest.main()
