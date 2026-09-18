"""
Rachel's Proactive Decision Support Orchestrator.
Coordinates:
- API layer (src.api: DataMallClient, WeatherClient)
- Routing layer (src.routing: MultimodalRouter, coordinates, walking legs)
- Intelligence layer (src.intelligence: personas, noise_filter, advisor, scenarios)
"""

from typing import Dict, Any, Optional

from .api.datamall_client import DataMallClient
from .api.weather_client import WeatherClient
from .routing.coordinates import (
    ORIGIN_POINT,
    DESTINATION_POINT,
    EWL_STATIONS,
    DTL_STATIONS,
    get_ewl_polyline,
    get_dtl_polyline,
    get_bus10e_polyline,
)
from .routing.door_to_door import get_walking_legs
from .routing.multimodal_router import MultimodalRouter
from .intelligence.personas import RACHEL_PROFILE
from .intelligence.noise_filter import evaluate_noise_filter
from .intelligence.advisor import synthesize_actionable_advice
from .intelligence.scenarios import (
    get_scenario,
    SCENARIOS,
    SCENARIO_NORMAL,
    SCENARIO_EWL_FAULT,
    SCENARIO_WEATHER_SURGE
)


class CommuterEngine:
    def __init__(self, datamall_client: Optional[DataMallClient] = None, weather_client: Optional[WeatherClient] = None):
        self.datamall = datamall_client or DataMallClient()
        self.weather = weather_client or WeatherClient()
        self.router = MultimodalRouter()
        self.current_scenario_id = SCENARIO_NORMAL
        self.use_live = False

    def set_scenario(self, scenario_id: str) -> bool:
        if scenario_id == "live":
            self.use_live = True
            self.current_scenario_id = "live"
            return True
        if scenario_id in SCENARIOS:
            self.use_live = False
            self.current_scenario_id = scenario_id
            return True
        return False

    def evaluate_commute(
        self,
        custom_arrival: Optional[str] = None,
        custom_origin: Optional[str] = None,
        custom_dest: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Orchestrates commute evaluation:
        1. Ingests current alerts (live or scenario)
        2. Computes journey times for primary and alternative routes
        3. Evaluates noise filter (delay threshold & deadline risk against target arrival)
        4. Synthesizes 1-line actionable advice
        """
        deadline_arrival = custom_arrival or RACHEL_PROFILE["deadline_arrival"]
        origin_name = custom_origin or RACHEL_PROFILE["origin"]
        dest_name = custom_dest or RACHEL_PROFILE["destination"]

        if self.use_live:
            alerts_data = self.datamall.get_train_service_alerts()
            weather_data = self.weather.get_commute_weather("Tampines", "City")
            pcd_data = self.datamall.get_pcd_realtime("EWL")

            disrupted_stations = []
            delay_min = 0
            for seg in alerts_data.get("AffectedSegments", []):
                if seg.get("Line", "").upper() == "EWL":
                    stns = [s.strip() for s in seg.get("Stations", "").split(",") if s.strip()]
                    disrupted_stations.extend(stns)
                    delay_min = 20

            crowd_levels = {item.get("Station", ""): item.get("CrowdLevel", "m") for item in pcd_data}
            source_badge = "LTA DataMall & Weather (Live)"
            simulated_time = "Live System Time"
        else:
            scenario = get_scenario(self.current_scenario_id)
            alerts_data = scenario["alerts"]
            weather_data = scenario["weather"]
            delay_min = scenario["delay_minutes"]
            disrupted_stations = scenario.get("disrupted_stations", [])
            crowd_levels = scenario["crowd_levels"]
            source_badge = scenario["badge"]
            simulated_time = scenario["simulated_time"]

        # 1. Routing calculation
        ewl_crowd = crowd_levels.get("EW2", "m")
        dtl_crowd = crowd_levels.get("DT32", "l")
        
        primary_ewl = self.router.compute_ewl_journey(delay_min, ewl_crowd, disrupted_stations)
        
        # 2. Noise Filter check
        noise_evaluation = evaluate_noise_filter(
            delay_minutes=delay_min,
            threshold_minutes=RACHEL_PROFILE["delay_threshold_min"],
            estimated_arrival=primary_ewl["estimated_arrival"],
            deadline_arrival=deadline_arrival
        )
        is_delayed = noise_evaluation["is_delayed"]

        bypass_dtl = self.router.compute_dtl_bypass(dtl_crowd, is_active_bypass=is_delayed)
        bypass_bus = self.router.compute_bus_bypass()

        # 3. Actionable Advice generation
        notice_text = alerts_data.get("Message", [{}])[0].get("Content", "") if alerts_data.get("Message") else ""
        advice = synthesize_actionable_advice(
            is_delayed=is_delayed,
            delay_minutes=delay_min,
            ewl_arrival=primary_ewl["estimated_arrival"],
            dtl_arrival=bypass_dtl["estimated_arrival"],
            raw_notice_text=notice_text
        )

        active_profile = {
            **RACHEL_PROFILE,
            "origin": origin_name,
            "destination": dest_name,
            "deadline_arrival": deadline_arrival
        }

        return {
            "profile": active_profile,
            "simulated_time": simulated_time,
            "source_badge": source_badge,
            "scenario_id": self.current_scenario_id,
            "decision": {
                **noise_evaluation,
                "delay_minutes": delay_min,
                "threshold_minutes": RACHEL_PROFILE["delay_threshold_min"],
                "headline": advice["headline"],
                "one_line_advice": advice["one_line_advice"],
                "active_recommendation": advice["active_recommendation"],
            },
            "routes": {
                "primary_ewl": primary_ewl,
                "bypass_dtl": bypass_dtl,
                "bypass_bus10e": bypass_bus,
            },
            "weather": weather_data,
            "disruption_feed": alerts_data,
            "map_layers": {
                "origin": ORIGIN_POINT,
                "destination": DESTINATION_POINT,
                "ewl_track": get_ewl_polyline(),
                "dtl_track": get_dtl_polyline(),
                "bus10e_track": get_bus10e_polyline(),
                "walking_legs": get_walking_legs(),
                "ewl_stations": EWL_STATIONS,
                "dtl_stations": DTL_STATIONS,
            }
        }
