"""
StationBuddy Proactive Decision Support Orchestrator.
Coordinates:
- API layer (src.api: DataMallClient, WeatherClient)
- Routing layer (src.routing: MultimodalRouter, coordinates, walking legs)
- Intelligence layer (src.intelligence: personas, noise_filter, advisor, scenarios, crowd_forecast)
"""

from typing import Dict, Any, Optional, List

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
from .intelligence.personas import (
    RACHEL_PROFILE,
    ARJUN_PROFILE,
    MDM_LIM_PROFILE,
    ALL_PERSONAS,
    get_persona,
    list_personas,
)
from .intelligence.noise_filter import evaluate_noise_filter
from .intelligence.advisor import synthesize_actionable_advice
from .intelligence.crowd_forecast import evaluate_pcd_forecast
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
        self.current_persona_id = "rachel"
        self.use_live = False

    def set_scenario(self, scenario_id: str) -> bool:
        """Switches active scenario mode (normal, ewl_fault, weather_surge, live)."""
        if scenario_id == "live":
            self.use_live = True
            self.current_scenario_id = "live"
            return True
        if scenario_id in SCENARIOS:
            self.use_live = False
            self.current_scenario_id = scenario_id
            return True
        return False

    def set_persona(self, persona_id: str) -> bool:
        """Switches active commuter persona (rachel, arjun, mdm_lim)."""
        clean_id = str(persona_id).strip().lower()
        if clean_id in ALL_PERSONAS:
            self.current_persona_id = clean_id
            return True
        return False

    def list_personas(self) -> List[Dict[str, Any]]:
        """Returns metadata for all available personas."""
        return list_personas()

    def evaluate_commute(
        self,
        custom_arrival: Optional[str] = None,
        custom_origin: Optional[str] = None,
        custom_dest: Optional[str] = None,
        custom_persona: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Orchestrates commute evaluation:
        1. Ingests current alerts & crowd forecasts (live or scenario)
        2. Computes journey times for active persona (Rachel, Arjun, Mdm Lim)
        3. Evaluates PCDForecast pre-emptive crowd shift advice
        4. Evaluates noise filter (delay threshold & deadline risk)
        5. Synthesizes 1-line actionable advice with AI summarizer
        """
        active_persona_id = custom_persona or self.current_persona_id
        base_profile = get_persona(active_persona_id)

        deadline_arrival = custom_arrival or base_profile.get("deadline_arrival", "08:45 AM")
        origin_name = custom_origin or base_profile.get("origin", "Blk 230 Tampines St 21")
        dest_name = custom_dest or base_profile.get("destination", "One Raffles Place, CBD")
        threshold_min = base_profile.get("delay_threshold_min", 15)
        dep_time = base_profile.get("departure_time", "07:40 AM")
        boarding_stn = base_profile.get("boarding_station", "EW2")

        if self.use_live:
            alerts_data = self.datamall.get_train_service_alerts()
            weather_data = self.weather.get_commute_weather("Tampines", "City")
            pcd_data = self.datamall.get_pcd_realtime(base_profile.get("primary_line", "EWL"))
            pcd_forecast_data = self.datamall.get_pcd_forecast(base_profile.get("primary_line", "EWL"))

            disrupted_stations = []
            delay_min = 0
            for seg in alerts_data.get("AffectedSegments", []):
                if seg.get("Line", "").upper() == base_profile.get("primary_line", "EWL"):
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
            pcd_forecast_data = scenario.get("pcd_forecast", [])
            source_badge = scenario["badge"]
            simulated_time = scenario["simulated_time"]

        # Evaluate PCDForecast pre-emptive crowd departure advisory
        crowd_forecast_eval = evaluate_pcd_forecast(
            forecast_data=pcd_forecast_data,
            station_code=boarding_stn,
            departure_time=dep_time,
            advance_lead_min=10,
        )
        pcd_forecast_warning = crowd_forecast_eval.get("advice") if crowd_forecast_eval.get("forecast_detected") else None

        # Route calculation per persona
        rain_active = weather_data.get("rain_alert", False)

        if active_persona_id == "arjun":
            arjun_journey = self.router.compute_arjun_journey(rain_active=rain_active, delay_minutes=delay_min)
            routes = {
                "primary_arjun": arjun_journey,
            }
            primary_eta = arjun_journey["estimated_arrival"]
            bypass_eta = arjun_journey["estimated_arrival"]

            noise_evaluation = evaluate_noise_filter(
                delay_minutes=delay_min,
                threshold_minutes=threshold_min,
                estimated_arrival=primary_eta,
                deadline_arrival=deadline_arrival,
            )
            is_delayed = noise_evaluation["is_delayed"]

        elif active_persona_id == "mdm_lim":
            lim_journey = self.router.compute_mdm_lim_journey(rain_active=rain_active)
            routes = {
                "primary_mdm_lim": lim_journey,
            }
            primary_eta = lim_journey["estimated_arrival"]
            bypass_eta = lim_journey["estimated_arrival"]

            noise_evaluation = evaluate_noise_filter(
                delay_minutes=delay_min,
                threshold_minutes=threshold_min,
                estimated_arrival=primary_eta,
                deadline_arrival=deadline_arrival,
            )
            is_delayed = noise_evaluation["is_delayed"]

        else:
            # Rachel (Default Corporate Commuter corridor)
            ewl_crowd = crowd_levels.get("EW2", "m")
            dtl_crowd = crowd_levels.get("DT32", "l")

            primary_ewl = self.router.compute_ewl_journey(delay_min, ewl_crowd, disrupted_stations)

            noise_evaluation = evaluate_noise_filter(
                delay_minutes=delay_min,
                threshold_minutes=threshold_min,
                estimated_arrival=primary_ewl["estimated_arrival"],
                deadline_arrival=deadline_arrival,
            )
            is_delayed = noise_evaluation["is_delayed"]

            bypass_dtl = self.router.compute_dtl_bypass(dtl_crowd, is_active_bypass=is_delayed)
            bypass_bus = self.router.compute_bus_bypass()

            routes = {
                "primary_ewl": primary_ewl,
                "bypass_dtl": bypass_dtl,
                "bypass_bus10e": bypass_bus,
            }
            primary_eta = primary_ewl["estimated_arrival"]
            bypass_eta = bypass_dtl["estimated_arrival"]

        # Actionable Advice Generation with AI / LLM Summarizer
        notice_text = alerts_data.get("Message", [{}])[0].get("Content", "") if alerts_data.get("Message") else ""
        advice = synthesize_actionable_advice(
            is_delayed=is_delayed,
            delay_minutes=delay_min,
            ewl_arrival=primary_eta,
            dtl_arrival=bypass_eta,
            raw_notice_text=notice_text,
            target_arrival=deadline_arrival,
            persona_id=active_persona_id,
            pcd_forecast_advice=pcd_forecast_warning,
        )

        active_profile = {
            **base_profile,
            "origin": origin_name,
            "destination": dest_name,
            "deadline_arrival": deadline_arrival,
            "delay_threshold_min": threshold_min,
        }

        return {
            "profile": active_profile,
            "simulated_time": simulated_time,
            "source_badge": source_badge,
            "scenario_id": self.current_scenario_id,
            "persona_id": active_persona_id,
            "pcd_forecast": crowd_forecast_eval,
            "decision": {
                **noise_evaluation,
                "delay_minutes": delay_min,
                "threshold_minutes": threshold_min,
                "headline": advice["headline"],
                "one_line_advice": advice["one_line_advice"],
                "active_recommendation": advice["active_recommendation"],
                "ai_metadata": advice.get("ai_metadata", {}),
            },
            "routes": routes,
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
