"""Behavioral tests for configurable profiles, routing and grounded advice."""

from copy import deepcopy
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import Mock

from src.intelligence import (
    ALL_PERSONAS, CommuterProfile, create_custom_user_route, get_persona,
    register_custom_persona, update_persona, save_personas, load_personas,
)
from src.intelligence.personas import get_active_persona, set_active_persona
from src.intelligence.advisor import synthesize_actionable_advice


def journey(**overrides):
    route = {
        "id": "test_route", "title": "Jurong East to Bishan", "line": "NSL",
        "lines_used": ["NSL"], "total_duration_min": 38, "delay_minutes": 0,
        "crowd_level": "m", "sheltered_percent": 100,
        "legs": [
            {"mode": "WALK", "duration": "10 min", "distance": "600m", "sheltered_percent": 100},
            {"mode": "TRAIN", "duration": "20 min"},
            {"mode": "WALK", "duration": "5 min", "distance": "300m", "sheltered_percent": 100},
        ],
    }
    route.update(overrides)
    return route


class TestCustomPersonas(unittest.TestCase):
    def setUp(self):
        self.originals = dict(ALL_PERSONAS)
        self.snapshot = deepcopy(ALL_PERSONAS)
        self.active = get_active_persona()["id"]
        self.router = Mock()
        self.router.route_arbitrary_commute.return_value = journey()

    def tearDown(self):
        for key, original in self.originals.items():
            original.clear()
            original.update(self.snapshot[key])
        ALL_PERSONAS.clear()
        ALL_PERSONAS.update(self.originals)
        set_active_persona(self.active)

    def route(self, **kwargs):
        return create_custom_user_route("Jurong East", "Bishan", router_instance=self.router, **kwargs)

    def test_duplicate_names_have_unique_ids(self):
        first = register_custom_persona({"name": "Alex"})
        second = register_custom_persona({"name": "Alex"})
        self.assertNotEqual(first["id"], second["id"])
        self.assertEqual(get_persona(first["id"])["name"], "Alex")

    def test_zero_threshold_false_string_and_independent_accessibility(self):
        profile = register_custom_persona({"delay_threshold_min": 0, "cycling_enabled": "false",
                                           "stair_aversion": True, "requires_step_free": False,
                                           "walking_speed_mps": 1.7, "crowd_tolerance": "high"})
        self.assertEqual(profile["delay_threshold_min"], 0)
        self.assertFalse(profile["cycling_enabled"])
        self.assertFalse(profile["requires_step_free"])
        self.assertFalse(profile["requires_lift_monitoring"])
        self.assertEqual(profile["walking_speed_mps"], 1.7)
        self.assertEqual(profile["crowd_tolerance"], "high")

    def test_invalid_profiles_do_not_register(self):
        original_ids = set(ALL_PERSONAS)
        for data in ({"walking_speed_mps": 0}, {"cycling_speed_mps": float("nan")},
                     {"delay_threshold_min": -1}, {"max_transfers": 1.5},
                     {"cycling_enabled": "maybe"}, {"departure_time": "25:80"},
                     {"rain_shelter_priority": 2}, {"walking_speeed_mps": 1}):
            with self.subTest(data=data), self.assertRaises(ValueError):
                register_custom_persona(data)
        self.assertEqual(set(ALL_PERSONAS), original_ids)

    def test_template_and_updates_preserve_identity(self):
        profile = register_custom_persona({"template_id": "arjun", "name": "Alex", "cycling_enabled": False})
        self.assertEqual(profile["origin"], get_persona("arjun")["origin"])
        self.assertFalse(profile["cycling_enabled"])
        edited = update_persona(profile["id"], {"walking_speed_mps": 1.8, "max_transfers": 1})
        self.assertEqual(edited["id"], profile["id"])
        self.assertEqual(get_persona(profile["id"])["walking_speed_mps"], 1.8)
        self.assertEqual(get_persona("arjun")["walking_speed_mps"], 1.4)

    def test_preset_edit_preserves_existing_import_reference(self):
        reference = ALL_PERSONAS["rachel"]
        update_persona("rachel", {"delay_threshold_min": 7})
        self.assertIs(reference, ALL_PERSONAS["rachel"])
        self.assertEqual(reference["delay_threshold_min"], 7)

    def test_derived_times_and_stale_bypass(self):
        profile = register_custom_persona({"template_id": "rachel", "origin": "Jurong East",
                                           "departure_time": "10:00", "normal_duration_min": 30,
                                           "arrival_buffer_min": 10, "proactive_lead_min": 15})
        self.assertEqual(profile["deadline_arrival"], "10:40 AM")
        self.assertEqual(profile["proactive_check_time"], "09:45 AM")
        self.assertIsNone(profile["alternative_route_name"])

    def test_registry_results_are_copies(self):
        profile = register_custom_persona({"name": "Alex"})
        profile["allowed_modes"].clear()
        retrieved = get_persona(profile["id"])
        retrieved["name"] = "Changed"
        self.assertEqual(get_persona(profile["id"])["name"], "Alex")
        self.assertTrue(get_persona(profile["id"])["allowed_modes"])

    def test_json_round_trip_and_validation_is_atomic(self):
        profile = register_custom_persona({"name": "Alex", "walking_speed_mps": 1.8})
        with tempfile.TemporaryDirectory(dir=Path(__file__).parent) as folder:
            path = Path(folder) / "personas.json"
            save_personas(str(path))
            update_persona(profile["id"], {"walking_speed_mps": 1.2})
            load_personas(str(path))
            self.assertEqual(get_persona(profile["id"])["walking_speed_mps"], 1.8)
            before = deepcopy(ALL_PERSONAS)
            payload = json.loads(path.read_text(encoding="utf-8"))
            payload["profiles"][0]["name"] = "Should not be applied"
            payload["profiles"][-1]["walking_speed_mps"] = -1
            path.write_text(json.dumps(payload), encoding="utf-8")
            with self.assertRaises(ValueError):
                load_personas(str(path))
            self.assertEqual(ALL_PERSONAS, before)

    def test_speed_recalculates_eta_without_mutating_router_result(self):
        before = deepcopy(self.router.route_arbitrary_commute.return_value)
        slow = self.route(walking_speed_mps=1)
        fast = self.route(walking_speed_mps=2)
        self.assertEqual(slow["route"]["total_duration_min"], 38)
        self.assertEqual(fast["route"]["total_duration_min"], 31)
        self.assertEqual(fast["route"]["estimated_arrival"], "08:31 AM")
        self.assertEqual(self.router.route_arbitrary_commute.return_value, before)

    def test_verified_cycling_option_recalculates_duration_and_rain_disables_it(self):
        self.router.route_arbitrary_commute.return_value["first_mile_cycle_leg"] = {
            "mode": "CYCLE", "duration": "10 min", "distance": "1.2km"}
        dry = self.route(cycling_enabled=True, walking_speed_mps=1, cycling_speed_mps=4)
        wet = self.route(cycling_enabled=True, walking_speed_mps=1, rain_active=True)
        self.assertEqual(dry["route"]["legs"][0]["mode"], "CYCLE")
        self.assertEqual(dry["route"]["total_duration_min"], 33)
        self.assertEqual(wet["route"]["legs"][0]["mode"], "WALK")
        self.assertFalse(wet["route"]["cycling_enabled"])

    def test_cycling_path_is_not_invented(self):
        result = self.route(cycling_enabled=True)
        self.assertFalse(result["route"]["cycling_enabled"])
        self.assertIn("no verified cycling path", result["route"]["warnings"][0])

    def test_required_accessibility_is_not_invented(self):
        result = self.route(requires_step_free=True)
        self.assertEqual(result["code"], "NO_FEASIBLE_ROUTE")
        self.assertFalse(result["candidate_routes"][0]["step_free_certified"])
        for leg in self.router.route_arbitrary_commute.return_value["legs"]:
            leg["step_free"] = True
        self.router.route_arbitrary_commute.return_value["lifts_operational"] = True
        self.assertEqual(self.route(requires_step_free=True, requires_lift_monitoring=True)["status"], "success")

    def test_modes_distance_and_transfer_limits_are_enforced(self):
        for preferences in ({"allowed_modes": ["WALK"]}, {"max_walking_distance_m": 100}):
            with self.subTest(preferences=preferences):
                self.assertEqual(self.route(**preferences)["code"], "NO_FEASIBLE_ROUTE")
        self.router.route_arbitrary_commute.return_value["transfers"] = 2
        self.assertEqual(self.route(max_transfers=1)["code"], "NO_FEASIBLE_ROUTE")

    def test_crowd_preference_changes_route_selection(self):
        alternative = journey(id="quiet_route", total_duration_min=43, crowd_level="l")
        alternative["legs"][1]["duration"] = "25 min"
        self.router.route_arbitrary_commute.return_value.update(crowd_level="h", alternatives=[alternative])
        self.assertEqual(self.route(crowd_tolerance="low")["route"]["id"], "quiet_route")
        self.assertEqual(self.route(crowd_tolerance="high")["route"]["id"], "test_route")

    def test_shelter_preference_changes_rain_route_selection(self):
        self.router.route_arbitrary_commute.return_value["sheltered_percent"] = 0
        self.router.route_arbitrary_commute.return_value["alternatives"] = [journey(id="covered_route", total_duration_min=43)]
        self.assertEqual(self.route(rain_active=True, rain_shelter_priority=1)["route"]["id"], "covered_route")
        self.assertEqual(self.route(rain_active=True, rain_shelter_priority=0)["route"]["id"], "test_route")

    def test_delayed_advice_preserves_route_selected_for_preferences(self):
        quiet = journey(id="quiet_route", total_duration_min=43, crowd_level="l", delay_minutes=25)
        quiet["legs"][1]["duration"] = "25 min"
        self.router.route_arbitrary_commute.return_value.update(crowd_level="h", delay_minutes=25, alternatives=[quiet])
        result = self.route(crowd_tolerance="low")
        self.assertEqual(result["route"]["id"], "quiet_route")
        self.assertEqual(result["decision"]["active_recommendation"], "quiet_route")
        self.assertIn(result["route"]["estimated_arrival"], result["decision"]["one_line_advice"])

    def test_overnight_deadline_and_day_offset(self):
        on_time = self.route(departure_time="23:40", deadline_arrival="00:30", walking_speed_mps=1)
        late = self.route(departure_time="23:40", deadline_arrival="23:55", walking_speed_mps=1)
        self.assertFalse(on_time["decision"]["is_delayed"])
        self.assertTrue(late["decision"]["is_delayed"])
        self.assertEqual(on_time["route"]["arrival_day_offset"], 1)
        self.assertIn("12 min before deadline", on_time["decision"]["one_line_advice"])

    def test_no_route_or_unknown_station_does_not_create_profile(self):
        original_ids = set(ALL_PERSONAS)
        self.router.route_arbitrary_commute.return_value = None
        self.assertEqual(self.route()["code"], "NO_ROUTE")
        unknown = create_custom_user_route("Unknownville", "Bishan", router_instance=self.router)
        self.assertEqual(unknown["code"], "UNKNOWN_STATION")
        self.assertEqual(set(ALL_PERSONAS), original_ids)

    def test_exact_station_name_and_station_codes(self):
        create_custom_user_route("Bedok North", "EW14", router_instance=self.router)
        self.router.route_arbitrary_commute.assert_called_with(
            origin_station="Bedok North", dest_station="Raffles Place", rain_active=False)

    def test_routing_does_not_switch_active_persona_or_edit_saved_profile(self):
        profile = register_custom_persona({"origin": "Jurong East", "destination": "Bishan"})
        before = get_persona(profile["id"])
        create_custom_user_route(profile=profile, walking_speed_mps=2, router_instance=self.router)
        self.assertEqual(get_active_persona()["id"], self.active)
        self.assertEqual(get_persona(profile["id"]), before)

    def test_advice_uses_custom_departure_route_and_tone(self):
        result = self.route(name="Alex", departure_time="10:05", advice_tone="friendly and reassuring")
        advice = result["decision"]["one_line_advice"]
        self.assertIn("10:05", advice)
        self.assertNotIn("07:40", advice)
        self.assertNotIn("Downtown Line", advice)
        prompt = result["decision"]["ai_metadata"]["llm_prompt"]
        self.assertIn("Alex", prompt)
        self.assertIn("friendly and reassuring", prompt)

    def test_delayed_custom_advice_does_not_invent_a_bypass(self):
        self.router.route_arbitrary_commute.return_value["delay_minutes"] = 25
        result = self.route()
        self.assertEqual(result["decision"]["active_recommendation"], "test_route")
        self.assertNotIn("Downtown", result["decision"]["one_line_advice"])

    def test_advice_respects_character_limit(self):
        result = self.route(advice_max_chars=40)
        advice = result["decision"]["one_line_advice"]
        self.assertLessEqual(len(advice), 40)
        self.assertIn(result["route"]["estimated_arrival"], advice)


if __name__ == "__main__":
    unittest.main()
