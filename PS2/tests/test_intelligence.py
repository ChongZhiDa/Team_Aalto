"""
Unit tests for Commuter Intelligence Module.
"""

import unittest
from src.intelligence.personas import RACHEL_PROFILE, get_persona
from src.intelligence.noise_filter import evaluate_noise_filter, UrgencyLevel
from src.intelligence.advisor import synthesize_actionable_advice
from src.intelligence.scenarios import get_scenario, list_scenarios, SCENARIO_EWL_FAULT


class TestIntelligenceModule(unittest.TestCase):
    def test_persona_profiles(self):
        rachel = get_persona("rachel")
        self.assertEqual(rachel["name"], "Rachel")
        self.assertEqual(rachel["delay_threshold_min"], 15)

    def test_noise_filter_suppresses_noise(self):
        # 2 minute delay, arrives 08:24 AM (well before 08:45 deadline)
        eval_result = evaluate_noise_filter(
            delay_minutes=2,
            threshold_minutes=15,
            estimated_arrival="08:24 AM",
            deadline_arrival="08:45 AM"
        )
        self.assertEqual(eval_result["urgency"], UrgencyLevel.CALM.value)
        self.assertEqual(eval_result["notification_action"], "SUPPRESSED")
        self.assertFalse(eval_result["is_delayed"])

    def test_noise_filter_triggers_critical_alert(self):
        # 25 minute delay, arrives 08:47 AM (past 08:45 deadline)
        eval_result = evaluate_noise_filter(
            delay_minutes=25,
            threshold_minutes=15,
            estimated_arrival="08:47 AM",
            deadline_arrival="08:45 AM"
        )
        self.assertEqual(eval_result["urgency"], UrgencyLevel.CRITICAL.value)
        self.assertEqual(eval_result["notification_action"], "PROACTIVE_PUSH_FIRED")
        self.assertTrue(eval_result["is_delayed"])

    def test_actionable_advice_synthesis(self):
        advice = synthesize_actionable_advice(
            is_delayed=True,
            delay_minutes=25,
            ewl_arrival="08:47 AM",
            dtl_arrival="08:24 AM"
        )
        self.assertIn("Downtown Line", advice["one_line_advice"])
        self.assertEqual(advice["active_recommendation"], "BYPASS_DTL")

    def test_scenarios_listing(self):
        scenarios = list_scenarios()
        self.assertGreaterEqual(len(scenarios), 3)
        fault_scenario = get_scenario(SCENARIO_EWL_FAULT)
        self.assertEqual(fault_scenario["delay_minutes"], 25)


if __name__ == "__main__":
    unittest.main()

