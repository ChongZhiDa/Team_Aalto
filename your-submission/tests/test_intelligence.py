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

    def test_minute_level_deadline_precision(self):
        # 1 minute past target triggers alert even if delay is minor
        eval_late = evaluate_noise_filter(
            delay_minutes=3,
            threshold_minutes=15,
            estimated_arrival="08:25 AM",
            deadline_arrival="08:24 AM"
        )
        self.assertTrue(eval_late["is_delayed"])
        self.assertEqual(eval_late["urgency"], UrgencyLevel.CRITICAL.value)

        # Arriving exactly on or before minute target stays calm (under delay threshold)
        eval_ontime = evaluate_noise_filter(
            delay_minutes=3,
            threshold_minutes=15,
            estimated_arrival="08:24 AM",
            deadline_arrival="08:24"  # 24h format supported
        )
        self.assertFalse(eval_ontime["is_delayed"])
        self.assertEqual(eval_ontime["urgency"], UrgencyLevel.CALM.value)

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

    def test_llm_prompt_generation(self):
        from src.intelligence.advisor import build_advisory_llm_prompt
        prompt = build_advisory_llm_prompt(
            raw_notice_text="[SMRT] EWL Update: track point fault at Kembangan.",
            commuter_name="Rachel",
            target_arrival="08:45 AM",
            primary_route_eta="08:47 AM",
            bypass_route_eta="08:24 AM",
            delay_minutes=25
        )
        self.assertIn("Rachel", prompt)
        self.assertIn("Downtown Line", prompt)
        self.assertIn("08:45 AM", prompt)
        self.assertIn("STRICT CONSTRAINTS", prompt)

    def test_notice_entity_extractor(self):
        from src.intelligence.advisor import extract_notice_entities
        text = "[SMRT] EWL Update: Due to a signalling fault near Kembangan, please add 25 to 30 mins travel time between Bedok and Bugis. Free regular bus service is available."
        entities = extract_notice_entities(text)
        self.assertEqual(entities["line"], "EWL")
        self.assertEqual(entities["delay_min"], 25)
        self.assertTrue(entities["free_bus"])
        self.assertEqual(entities["segment"], "Bedok to Bugis")

    def test_pcd_forecast_departure_advise_logic(self):
        from src.intelligence.crowd_forecast import evaluate_pcd_forecast
        forecast = [
            {"Station": "EW2", "StartTime": "08:00", "EndTime": "08:30", "CrowdLevel": "h"}
        ]
        res = evaluate_pcd_forecast(forecast_data=forecast, station_code="EW2", departure_time="07:40 AM")
        self.assertTrue(res["forecast_detected"])
        self.assertEqual(res["suggested_departure"], "07:30 AM")

        # Normal low crowd does not trigger advance departure
        normal_forecast = [
            {"Station": "EW2", "StartTime": "08:00", "EndTime": "08:30", "CrowdLevel": "l"}
        ]
        res_normal = evaluate_pcd_forecast(forecast_data=normal_forecast, station_code="EW2", departure_time="07:40 AM")
        self.assertFalse(res_normal["forecast_detected"])
        self.assertEqual(res_normal["suggested_departure"], "07:40 AM")


if __name__ == "__main__":
    unittest.main()


