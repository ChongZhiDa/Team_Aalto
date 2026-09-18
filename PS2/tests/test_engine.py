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


class TestIntelligenceAcceptance(unittest.TestCase):
    def setUp(self):
        self.engine = CommuterEngine()
        self.default_threshold = RACHEL_PROFILE["delay_threshold_min"]  # 15 min

    def test_tc_flt_01_noise_filter_suppression(self):
        """TC-FLT-01: Minor delays (<15 min) should be silenced to prevent alert fatigue."""
        from src.intelligence.noise_filter import evaluate_noise_filter, UrgencyLevel
        res = evaluate_noise_filter(
            delay_minutes=2,
            threshold_minutes=self.default_threshold,
            estimated_arrival="08:24 AM",
            deadline_arrival="08:45 AM",
        )
        self.assertEqual(res["notification_action"], "SUPPRESSED")
        self.assertEqual(res["urgency"], UrgencyLevel.CALM.value)
        self.assertFalse(res["is_delayed"])

    def test_tc_flt_02_noise_filter_trigger(self):
        """TC-FLT-02: Delays >= 15 min must fire a proactive alert with recommended bypass."""
        from src.intelligence.noise_filter import evaluate_noise_filter, UrgencyLevel
        res = evaluate_noise_filter(
            delay_minutes=25,
            threshold_minutes=self.default_threshold,
            estimated_arrival="08:47 AM",
            deadline_arrival="08:45 AM",
        )
        self.assertEqual(res["notification_action"], "PROACTIVE_PUSH_FIRED")
        self.assertEqual(res["urgency"], UrgencyLevel.CRITICAL.value)
        self.assertTrue(res["is_delayed"])

    def test_tc_flt_03_dynamic_threshold_adjustment(self):
        """TC-FLT-03: User-adjusted threshold adapts engine sensitivity immediately."""
        from src.intelligence.noise_filter import evaluate_noise_filter
        res = evaluate_noise_filter(
            delay_minutes=12,
            threshold_minutes=10,  # Lowered sensitivity
            estimated_arrival="08:36 AM",
            deadline_arrival="08:45 AM",
        )
        self.assertTrue(res["is_delayed"])

    def test_tc_scn_01_baseline_commute_loading(self):
        """TC-SCN-01: Normal scenario loads Rachel's baseline Tampines -> Raffles commute."""
        res = self.engine.evaluate_commute()
        self.assertIn("primary_ewl", res["routes"])
        self.assertTrue(res["routes"]["primary_ewl"]["is_recommended"])

    def test_tc_scn_02_scenario_switch_bypass(self):
        """TC-SCN-02: EWL fault scenario activates DTL bypass arriving by 08:24 AM."""
        self.engine.set_scenario(SCENARIO_EWL_FAULT)
        res = self.engine.evaluate_commute()
        self.assertTrue(res["routes"]["bypass_dtl"]["is_recommended"])
        self.assertIn("Downtown Line", res["decision"]["one_line_advice"])

    def test_tc_per_01_persona_profiles_available(self):
        """TC-PER-01: Ensure Rachel, Arjun, and Mdm Lim profiles are defined."""
        from src.intelligence.personas import get_persona
        for p_id in ["rachel", "arjun", "mdm_lim"]:
            profile = get_persona(p_id)
            self.assertIsNotNone(profile)
            self.assertIn("name", profile)

    def test_tc_ai_01_telegram_unstructured_notice_summarization(self):
        """TC-AI-01: AI/LLM summarizer ingests raw Telegram notice and outputs clean 1-line advice."""
        from src.intelligence.advisor import synthesize_actionable_advice
        raw_telegram = (
            "[SMRT] EWL Update: Due to a signalling fault near Kembangan, train service "
            "between Bedok and Bugis is delayed by up to 25-30 mins. Free regular bus services "
            "are running at designated bus stops. Station staff are assisting. We apologise "
            "for the inconvenience caused. #SMRT"
        )
        advice = synthesize_actionable_advice(
            is_delayed=True,
            delay_minutes=25,
            ewl_arrival="08:47 AM",
            dtl_arrival="08:24 AM",
            raw_notice_text=raw_telegram,
            target_arrival="08:45 AM",
            persona_id="rachel"
        )
        self.assertIn("Downtown Line", advice["one_line_advice"])
        self.assertIn("ai_metadata", advice)
        self.assertGreaterEqual(float(advice["ai_metadata"]["compression_ratio"].replace("%", "")), 40.0)

    def test_tc_pcd_01_preemptive_crowd_departure_advice(self):
        """TC-PCD-01: High platform crowd forecast ('h') at 08:00 AM advises 10-min advance departure."""
        from src.intelligence.crowd_forecast import evaluate_pcd_forecast
        pcd_data = [
            {"Station": "EW2", "StartTime": "08:00", "EndTime": "08:30", "CrowdLevel": "h"}
        ]
        result = evaluate_pcd_forecast(
            forecast_data=pcd_data,
            station_code="EW2",
            departure_time="07:40 AM",
            advance_lead_min=10
        )
        self.assertTrue(result["forecast_detected"])
        self.assertEqual(result["suggested_departure"], "07:30 AM")
        self.assertIn("leave 10 mins early at 07:30 AM to beat the rush", result["advice"])

    def test_tc_per_02_engine_persona_switching_arjun(self):
        """TC-PER-02: Switching to Arjun routes multimodal cycle + transit to one-north."""
        self.engine.set_persona("arjun")
        res = self.engine.evaluate_commute()
        self.assertEqual(res["persona_id"], "arjun")
        self.assertIn("primary_arjun", res["routes"])
        self.assertEqual(res["profile"]["name"], "Arjun")
        self.assertTrue(res["routes"]["primary_arjun"]["is_recommended"])

    def test_tc_per_03_engine_persona_switching_mdm_lim(self):
        """TC-PER-03: Switching to Mdm Lim routes step-free accessibility transit."""
        self.engine.set_persona("mdm_lim")
        res = self.engine.evaluate_commute()
        self.assertEqual(res["persona_id"], "mdm_lim")
        self.assertIn("primary_mdm_lim", res["routes"])
        self.assertEqual(res["profile"]["name"], "Mdm Lim")
        self.assertTrue(res["routes"]["primary_mdm_lim"]["step_free_certified"])


if __name__ == "__main__":
    unittest.main()


