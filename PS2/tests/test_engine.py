"""
Unit tests for Rachel's Smart Commuter Companion Engine.
Verifies noise filtering, line normalization, scenario transitions, and arrival calculations.
"""

import unittest
from src.canonical_lines import (
    normalize_alert_line,
    normalize_pcd_line,
    LINE_EWL,
    LINE_SKL,
    LINE_PGL,
    LINE_DTL,
)
from src.engine import CommuterEngine, RACHEL_PROFILE
from src.scenarios import (
    SCENARIO_NORMAL,
    SCENARIO_EWL_FAULT,
    SCENARIO_WEATHER_SURGE,
)


class TestCommuterCompanion(unittest.TestCase):
    def setUp(self):
        self.engine = CommuterEngine()

    def test_canonical_line_mapping(self):
        """Checks normalization of disparate line codes between endpoints."""
        # TrainServiceAlerts codes
        self.assertEqual(normalize_alert_line("STL"), LINE_SKL)
        self.assertEqual(normalize_alert_line("PTL"), LINE_PGL)
        self.assertEqual(normalize_alert_line("EWL"), LINE_EWL)
        self.assertEqual(normalize_alert_line("DTL"), LINE_DTL)

        # PCD codes
        self.assertEqual(normalize_pcd_line("SLRT"), LINE_SKL)
        self.assertEqual(normalize_pcd_line("PLRT"), LINE_PGL)
        self.assertEqual(normalize_pcd_line("CGL"), LINE_EWL)

    def test_noise_filter_suppression_normal_commute(self):
        """Under normal commute, minor delays (<15 min) should be filtered as noise."""
        self.engine.set_scenario(SCENARIO_NORMAL)
        res = self.engine.evaluate_commute()

        decision = res["decision"]
        self.assertEqual(decision["urgency"], "CALM")
        self.assertEqual(decision["notification_action"], "SUPPRESSED")
        self.assertFalse(decision["is_delayed"])
        self.assertEqual(decision["active_recommendation"], "PRIMARY_EWL")
        self.assertIn("On track", decision["headline"])

    def test_proactive_alert_on_major_disruption(self):
        """When delay >= 15 min, engine must fire proactive alert with DTL bypass."""
        self.engine.set_scenario(SCENARIO_EWL_FAULT)
        res = self.engine.evaluate_commute()

        decision = res["decision"]
        self.assertEqual(decision["urgency"], "CRITICAL")
        self.assertEqual(decision["notification_action"], "PROACTIVE_PUSH_FIRED")
        self.assertTrue(decision["is_delayed"])
        self.assertEqual(decision["active_recommendation"], "BYPASS_DTL")
        
        # Check routes
        routes = res["routes"]
        self.assertTrue(routes["bypass_dtl"]["is_recommended"])
        self.assertFalse(routes["primary_ewl"]["is_recommended"])
        self.assertIn("Downtown Line", decision["one_line_advice"])

    def test_weather_and_crowd_surge(self):
        """Monsoon rain and crowd surge should trigger rain alerts and delay warnings."""
        self.engine.set_scenario(SCENARIO_WEATHER_SURGE)
        res = self.engine.evaluate_commute()

        weather = res["weather"]
        self.assertTrue(weather["rain_alert"])
        self.assertTrue(res["decision"]["is_delayed"])

    def test_dynamic_threshold_adjustment(self):
        """Dynamic threshold changes affect alert trigger sensitivity."""
        self.engine.set_scenario(SCENARIO_NORMAL)
        # Normal has 2 min delay. If threshold is lowered to 1 min, it triggers an alert.
        RACHEL_PROFILE["delay_threshold_min"] = 1
        res = self.engine.evaluate_commute()
        self.assertTrue(res["decision"]["is_delayed"])

        # Reset threshold to default 15
        RACHEL_PROFILE["delay_threshold_min"] = 15
        res = self.engine.evaluate_commute()
        self.assertFalse(res["decision"]["is_delayed"])


if __name__ == "__main__":
    unittest.main()

