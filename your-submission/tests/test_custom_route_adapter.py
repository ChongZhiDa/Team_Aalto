"""
Unit and API integration tests for Flask Custom Route Adapter.
"""

import json
import os
import tempfile
import unittest
from flask import Flask

from src.intelligence.custom_route_adapter import custom_route_bp


class TestCustomRouteAdapter(unittest.TestCase):
    def setUp(self):
        self.app = Flask(__name__)
        self.app.register_blueprint(custom_route_bp)
        self.client = self.app.test_client()

    def test_get_custom_personas(self):
        resp = self.client.get("/api/custom/personas")
        self.assertEqual(resp.status_code, 200)
        data = resp.get_json()
        self.assertEqual(data["status"], "success")
        self.assertIn("personas", data)
        self.assertTrue(len(data["personas"]) >= 3)
        ids = [p["id"] for p in data["personas"]]
        self.assertIn("rachel", ids)
        self.assertIn("arjun", ids)
        self.assertIn("mdm_lim", ids)

    def test_custom_route_success(self):
        payload = {
            "origin": "Jurong East",
            "destination": "Bishan",
            "departure_time": "08:15",
            "deadline_arrival": "09:15",
            "cycling_enabled": False,
        }
        resp = self.client.post("/api/custom/route", json=payload)
        self.assertEqual(resp.status_code, 200)
        data = resp.get_json()
        self.assertEqual(data["status"], "success")
        self.assertIn("route", data)
        self.assertIn("decision", data)
        self.assertIn("headline", data["decision"])
        self.assertIn("one_line_advice", data["decision"])
        self.assertTrue(len(data["route"]["legs"]) >= 1)

    def test_custom_route_unknown_station(self):
        payload = {
            "origin": "FakeStation9999",
            "destination": "Bishan",
        }
        resp = self.client.post("/api/custom/route", json=payload)
        self.assertEqual(resp.status_code, 404)
        data = resp.get_json()
        self.assertEqual(data["status"], "error")
        self.assertEqual(data["code"], "UNKNOWN_STATION")

    def test_custom_route_no_feasible_route(self):
        payload = {
            "origin": "Pasir Ris",
            "destination": "Jurong East",
            "allowed_modes": ["WALK"],  # Impossible to walk across Singapore without violating constraints
            "max_walking_distance_m": 500
        }
        resp = self.client.post("/api/custom/route", json=payload)
        self.assertEqual(resp.status_code, 422)
        data = resp.get_json()
        self.assertEqual(data["status"], "error")
        self.assertEqual(data["code"], "NO_FEASIBLE_ROUTE")

    def test_register_and_update_custom_persona(self):
        new_persona = {
            "name": "Sarah",
            "origin": "Tampines",
            "destination": "City Hall",
            "departure_time": "08:00",
            "delay_threshold_min": 10
        }
        resp = self.client.post("/api/custom/personas", json=new_persona)
        self.assertEqual(resp.status_code, 201)
        data = resp.get_json()
        self.assertEqual(data["status"], "success")
        p_id = data["profile"]["id"]

        # Update
        up_resp = self.client.put(f"/api/custom/personas/{p_id}", json={"delay_threshold_min": 20})
        self.assertEqual(up_resp.status_code, 200)
        up_data = up_resp.get_json()
        self.assertEqual(up_data["profile"]["delay_threshold_min"], 20)

    def test_save_and_load_personas(self):
        with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as f:
            temp_path = f.name

        try:
            save_resp = self.client.post("/api/custom/personas/save", json={"filepath": temp_path})
            self.assertEqual(save_resp.status_code, 200)
            self.assertTrue(os.path.exists(temp_path))

            load_resp = self.client.post("/api/custom/personas/load", json={"filepath": temp_path})
            self.assertEqual(load_resp.status_code, 200)
            self.assertIn("personas", load_resp.get_json())
        finally:
            if os.path.exists(temp_path):
                os.remove(temp_path)


if __name__ == "__main__":
    unittest.main()

