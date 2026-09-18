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
from src.routing.location_resolver import resolve_location


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

    # --- Teammate 2 Extra: Nearest Station Lookup & Station Footprint Polygons ---
    def test_tc_rot_05_find_nearest_station_and_polygon(self):
        """TC-ROT-05: Verifies spatial nearest-station lookup and boundary polygon retrieval."""
        from src.routing.geojson_loader import find_nearest_station, get_station_polygon
        stn, dist_m = find_nearest_station(1.3533, 103.9452)
        self.assertIsNotNone(stn)
        self.assertEqual(stn["name"], "TAMPINES")
        self.assertLess(dist_m, 500)

        poly = get_station_polygon("Tampines")
        self.assertIsNotNone(poly)
        self.assertGreater(len(poly), 10, "Polygon must contain outer ring coordinates.")

    # --- Teammate 2 Extra: Arjun's Multi-Modal Cycling & Rain Adaptation ---
    def test_tc_rot_06_arjun_multimodal_cycling_and_rain(self):
        """TC-ROT-06: Verifies Arjun's multimodal commute dynamically shifts between cycling and rain mode."""
        # Good weather: 4m cycling leg
        dry = self.router.compute_arjun_journey(rain_active=False)
        self.assertTrue(dry["cycling_enabled"])
        self.assertEqual(dry["legs"][0]["mode"], "CYCLE")
        self.assertEqual(dry["total_duration_min"], 44)

        # Monsoon rain: Swaps open cycling to sheltered LRT linkway
        wet = self.router.compute_arjun_journey(rain_active=True)
        self.assertFalse(wet["cycling_enabled"])
        self.assertEqual(wet["legs"][0]["mode"], "WALK")
        self.assertIn("Rain", wet["status"])

    # --- Teammate 2 Extra: Mdm Lim's Accessibility & Lift Maintenance Warning ---
    def test_tc_rot_07_mdm_lim_step_free_and_lift_outage(self):
        """TC-ROT-07: Verifies step-free path certification and lift breakdown rerouting for Mdm Lim."""
        # Baseline normal: step-free certified
        normal = self.router.compute_mdm_lim_journey(rain_active=False)
        self.assertTrue(normal["step_free_certified"])
        self.assertFalse(normal["has_lift_alert"])
        self.assertEqual(normal["total_duration_min"], 43)

        # Lift maintenance at Outram Park: triggers warning and reroutes to ramp (+4m)
        outage = self.router.compute_mdm_lim_journey(rain_active=False, lift_outages=["OUTRAM PARK"])
        self.assertTrue(outage["has_lift_alert"])
        self.assertIn("Lift out of service", outage["status"])
        self.assertEqual(outage["total_duration_min"], 47)

    # --- Teammate 2 Extra: Fuzzy Matching for Stations & Landmarks ---
    def test_tc_rot_08_fuzzy_station_and_landmark_matching(self):
        """TC-ROT-08: Verifies fuzzy matching for MRT station names and landmarks."""
        all_stations = self.graph_router.get_all_station_names()

        # Station names with extra noise
        res_mrt = resolve_location("jurong east mrt station", all_stations)
        self.assertIsNotNone(res_mrt)
        self.assertEqual(res_mrt["station"], "Jurong East")

        # Hyphenated / casing variance
        res_on = resolve_location("one north", all_stations)
        self.assertIsNotNone(res_on)
        self.assertEqual(res_on["station"], "one-north")

        # Major landmarks and abbreviations
        res_nus = resolve_location("NUS", all_stations)
        self.assertIsNotNone(res_nus)
        self.assertEqual(res_nus["station"], "Kent Ridge")

        res_sgh = resolve_location("SGH", all_stations)
        self.assertIsNotNone(res_sgh)
        self.assertEqual(res_sgh["station"], "Outram Park")

    # --- Teammate 2 Extra: Postal Code Address Resolution & Door-to-Door Routing ---
    def test_tc_rot_09_postal_code_address_resolution(self):
        """TC-ROT-09: Verifies 6-digit Singapore postal code resolution to exact house address and door-to-door transit legs."""
        # Standalone postal code -> resolves to exact HDB block / building
        res_postal = resolve_location("341106")
        self.assertIsNotNone(res_postal)
        self.assertIn(res_postal["match_type"], ["exact_doorstep_address", "postal_code"])
        self.assertIn("106A", res_postal["display"])
        self.assertEqual(res_postal["station"], "Potong Pasir")
        self.assertGreater(res_postal["walk_m"], 0)

        # 'S' prefix format
        res_sprefix = resolve_location("S018956")
        self.assertIsNotNone(res_sprefix)
        self.assertIn(res_sprefix["station"], ["Raffles Place", "Bayfront"])

        # Door-to-door routing starting from exact house address
        route = self.router.route_door_to_door(
            "Blk 106A Bidadari Park Dr Singapore 341106",
            "10 Bayfront Avenue Singapore 018956"
        )
        self.assertFalse(route.get("error", True))
        # First leg is a walk from the exact house address to the next transport node (Potong Pasir MRT)
        self.assertEqual(route["legs"][0]["mode"], "WALK")
        self.assertIn("106A Bidadari", route["legs"][0]["name"])
        self.assertIn("Potong Pasir", route["legs"][0]["name"])
        self.assertGreater(route["total_duration_min"], 0)

    # --- Postal Sectors, NTU 639798 & Polyline Attachment Tests ---
    def test_tc_rot_10_postal_sectors_and_ntu_resolution(self):
        """TC-ROT-10: Verifies postal sector mappings for Bedok (46-48) and Jurong/Pioneer (60-64), and NTU 639798."""
        from src.routing.location_resolver import resolve_location, get_pedestrian_path

        # 6-digit postal code for NTU
        ntu_exact = resolve_location("639798")
        self.assertIsNotNone(ntu_exact)
        self.assertEqual(ntu_exact["station"], "Pioneer")
        self.assertIn("coordinates", ntu_exact)

        # Full address / landmark string with postal code
        ntu_full = resolve_location("639798 (Nanyang Technological University - NTU)")
        self.assertIsNotNone(ntu_full)
        self.assertEqual(ntu_full["station"], "Pioneer")

        # District 16 (Bedok / Upper East Coast)
        self.assertEqual(resolve_location("460123")["station"], "Bedok")
        self.assertEqual(resolve_location("470123")["station"], "Bedok")
        self.assertEqual(resolve_location("480123")["station"], "Bedok Reservoir")

        # District 22 (Jurong / Tuas / Pioneer / Boon Lay)
        self.assertEqual(resolve_location("600123")["station"], "Jurong East")
        self.assertEqual(resolve_location("610123")["station"], "Boon Lay")
        self.assertEqual(resolve_location("620123")["station"], "Joo Koon")
        self.assertEqual(resolve_location("630123")["station"], "Pioneer")
        self.assertEqual(resolve_location("640123")["station"], "Boon Lay")

        # Doorstep pedestrian path calculation
        waypoints, dist_m = get_pedestrian_path([1.3483, 103.6831], [1.3376, 103.6974])
        self.assertEqual(len(waypoints), 2)
        self.assertGreater(dist_m, 1000)

    def test_tc_rot_11_custom_and_door_to_door_polyline_attachment(self):
        """TC-ROT-11: Verifies custom router and door-to-door router attach polyline and station coordinates."""
        from src.intelligence.custom_router import create_custom_user_route

        # Custom route from NTU postal code to Raffles Place
        custom_res = create_custom_user_route(
            origin="639798 (Nanyang Technological University - NTU)",
            destination="Raffles Place"
        )
        self.assertEqual(custom_res["status"], "success")
        self.assertEqual(custom_res["profile"]["boarding_station"], "Pioneer")
        self.assertEqual(custom_res["profile"]["alighting_station"], "Raffles Place")

        route = custom_res["route"]
        self.assertIn("polyline", route)
        self.assertGreater(len(route["polyline"]), 5, "Polyline must have coordinates along the Western EWL corridor.")
        self.assertIn("stations", route)
        self.assertGreaterEqual(len(route["stations"]), 10)
        self.assertEqual(route["stations"][0]["name"].upper(), "PIONEER")

        # Multimodal door-to-door router attaches polyline coordinates
        d2d = self.router.route_door_to_door("639798 (Nanyang Technological University - NTU)", "One Raffles Place, CBD")
        self.assertFalse(d2d.get("error"))
        self.assertIn("polyline", d2d)
        self.assertGreater(len(d2d["polyline"]), 5)
        self.assertIn("stations", d2d)
        self.assertEqual(d2d["origin_resolved"]["station"], "Pioneer")


if __name__ == "__main__":
    unittest.main()

