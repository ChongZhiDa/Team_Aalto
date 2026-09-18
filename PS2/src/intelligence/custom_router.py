"""Profile-driven routing with explicit constraints and no implicit persona switching."""

from copy import deepcopy
from datetime import timedelta
import math
import re
from typing import Any, Dict, List, Optional, Union
from uuid import uuid4

from .personas import (
    ALL_PERSONAS, CommuterProfile, extract_station_name, get_persona,
    parse_profile_time, register_custom_persona, set_active_persona,
)
from .noise_filter import evaluate_noise_filter
from .advisor import synthesize_actionable_advice
from .crowd_forecast import evaluate_pcd_forecast


def _parse_time_to_minutes(time_str: str) -> int:
    parsed = parse_profile_time(time_str)
    return parsed.hour * 60 + parsed.minute


def _minutes_to_time_str(total_minutes: int) -> str:
    return (parse_profile_time("00:00") + timedelta(minutes=total_minutes)).strftime("%I:%M %p")


def _number(value: Any, unit: str) -> float:
    """Read structured numbers or legacy '350m' / '4 min' strings."""
    if isinstance(value, (int, float)) and not isinstance(value, bool):
        number = float(value)
    else:
        match = re.fullmatch(r"\s*(\d+(?:\.\d+)?)\s*(km|m|min)?\s*", str(value), re.I)
        if not match:
            raise ValueError(f"Invalid route {unit}: {value!r}")
        number = float(match.group(1))
        if unit == "distance" and (match.group(2) or "").lower() == "km":
            number *= 1000
    if not math.isfinite(number) or number < 0:
        raise ValueError(f"Invalid route {unit}: {value!r}")
    return number


def _resolve_station(query: str) -> Optional[str]:
    from ..routing.graph_router import MRT_LINES
    stations = [station for line in MRT_LINES.values() for station in line]
    for station in stations:
        if query.lower() in (station["code"].lower(), station["name"].lower()):
            return station["name"]
    candidate = extract_station_name(query, default="")
    for station in stations:
        if candidate.lower() == station["name"].lower():
            return station["name"]
    return None


def _adapt_route(route: Dict[str, Any], profile: CommuterProfile,
                 rain_active: bool, departure_minutes: int) -> Dict[str, Any]:
    route = deepcopy(route)
    route.pop("alternatives", None)
    legs = route.get("legs", [])
    if not legs:
        raise ValueError("Router returned a route without journey legs")
    old_total = sum(_number(leg.get("duration_min", leg.get("duration", 0)), "duration") for leg in legs)
    overhead = max(0, float(route.get("total_duration_min", old_total)) - old_total)
    cycling = (profile.cycling_enabled and "CYCLE" in profile.allowed_modes
               and not (rain_active and profile.avoid_cycling_in_rain))
    if cycling and legs[0].get("mode", "").upper() == "WALK":
        if route.get("first_mile_cycle_leg"):
            legs[0] = deepcopy(route["first_mile_cycle_leg"])
            legs[0]["mode"] = "CYCLE"
        else:
            route.setdefault("warnings", []).append("Cycling requested; no verified cycling path was supplied.")
    for leg in legs:
        mode = str(leg.get("mode", "")).upper()
        leg["mode"] = mode
        duration = _number(leg.get("duration_min", leg.get("duration", 0)), "duration")
        distance = leg.get("distance_m", leg.get("distance"))
        if distance is not None:
            leg["distance_m"] = _number(distance, "distance")
            if mode in ("WALK", "CYCLE"):
                speed = profile.walking_speed_mps if mode == "WALK" else profile.cycling_speed_mps
                duration = leg["distance_m"] / speed / 60
                if rain_active and mode == "WALK":
                    duration *= 1 + 0.3 * (1 - float(leg.get("sheltered_percent", 0)) / 100)
        leg["duration_min"] = round(duration, 2)
        leg["duration"] = f"{leg['duration_min']:g} min"
    route["total_duration_min"] = math.ceil(overhead + sum(leg["duration_min"] for leg in legs))
    route["estimated_arrival"] = _minutes_to_time_str(departure_minutes + route["total_duration_min"])
    route["arrival_day_offset"] = (departure_minutes + route["total_duration_min"]) // 1440
    route["cycling_enabled"] = any(leg["mode"] == "CYCLE" for leg in legs)
    route["step_free_certified"] = all(leg.get("step_free") is True for leg in legs)
    route["accessibility_status"] = "verified" if route["step_free_certified"] else "unverified"
    walking = [leg for leg in legs if leg["mode"] == "WALK"]
    route["walking_distance_m"] = sum(leg.get("distance_m", 0) for leg in walking)
    route["transfers"] = int(route.get("transfers", max(0, sum(leg["mode"] == "TRAIN" for leg in legs) - 1)))
    violations = []
    if any(leg["mode"] not in profile.allowed_modes for leg in legs):
        violations.append("Route uses a mode outside allowed_modes")
    if route["cycling_enabled"] and (not profile.cycling_enabled or (rain_active and profile.avoid_cycling_in_rain)):
        violations.append("Cycling is disabled for this journey")
    if profile.max_walking_distance_m is not None:
        if any("distance_m" not in leg for leg in walking):
            violations.append("Walking distance could not be verified")
        elif route["walking_distance_m"] > profile.max_walking_distance_m:
            violations.append("Route exceeds max_walking_distance_m")
    if profile.max_transfers is not None and route["transfers"] > profile.max_transfers:
        violations.append("Route exceeds max_transfers")
    if profile.requires_step_free and not route["step_free_certified"]:
        violations.append("Step-free access could not be verified for every leg")
    if profile.requires_lift_monitoring and route.get("lifts_operational") is not True:
        violations.append("Lift operation could not be verified")
    if profile.stair_aversion and not route["step_free_certified"]:
        route.setdefault("warnings", []).append("Stair avoidance requested; accessibility remains unverified.")
    route["constraint_violations"] = violations
    route["is_recommended"] = not violations
    return route


def _route_score(route: Dict[str, Any], profile: CommuterProfile, rain_active: bool) -> float:
    crowd_cost = {"low": 20, "normal": 8, "high": 0}[profile.crowd_tolerance]
    crowd = {"l": 0, "m": 0.5, "h": 1}.get(str(route.get("crowd_level", "m")).lower(), 0.5)
    shelter = float(route.get("sheltered_percent", 0)) / 100
    stair_cost = 10 if profile.stair_aversion and not route["step_free_certified"] else 0
    return (route["total_duration_min"] + crowd_cost * crowd + stair_cost
            + (20 * profile.rain_shelter_priority * (1 - shelter) if rain_active else 0))


def create_custom_user_route(
    origin: Optional[str] = None, destination: Optional[str] = None,
    name: Optional[str] = None, departure_time: Optional[str] = None,
    deadline_arrival: Optional[str] = None, delay_threshold_min: Optional[int] = None,
    cycling_enabled: Optional[bool] = None, stair_aversion: Optional[bool] = None,
    rain_active: bool = False, weather_summary: Optional[str] = None,
    raw_notice_text: str = "", pcd_forecast_data: Optional[List[Dict[str, Any]]] = None,
    router_instance: Optional[Any] = None,
    profile: Optional[Union[CommuterProfile, Dict[str, Any]]] = None,
    activate_profile: bool = False, **profile_overrides: Any,
) -> Dict[str, Any]:
    """Accept a full profile or legacy arguments, with independently editable settings.

    Routers may supply alternatives and a first_mile_cycle_leg. Mandatory
    constraints must be verified; no synthetic successful route is returned.
    """
    values = profile.to_dict() if isinstance(profile, CommuterProfile) else deepcopy(profile or {})
    template_id = values.pop("template_id", None)
    if template_id:
        values = {**get_persona(template_id, strict=True), **values}
        values.pop("id", None)
        values["is_custom"] = True
    explicit = dict(profile_overrides)
    for key, value in (("origin", origin), ("destination", destination), ("name", name),
                       ("departure_time", departure_time), ("deadline_arrival", deadline_arrival),
                       ("delay_threshold_min", delay_threshold_min), ("cycling_enabled", cycling_enabled),
                       ("stair_aversion", stair_aversion)):
        if value is not None:
            explicit[key] = value
    values.update(explicit)
    values.setdefault("id", f"custom_{uuid4().hex}")
    values.setdefault("name", "New Commuter")
    values.setdefault("persona", "Custom Commuter")
    if not values.get("origin") or not values.get("destination"):
        raise ValueError("origin and destination are required")
    commuter = CommuterProfile.from_dict(values)
    for location, station in (("origin", "boarding_station"), ("destination", "alighting_station")):
        query = values[station] if station in values and location not in explicit else values[location]
        resolved = _resolve_station(query)
        if not resolved:
            return {"status": "error", "code": "UNKNOWN_STATION",
                    "message": f"Cannot resolve {query!r} to a known MRT station"}
        setattr(commuter, station, resolved)
    dep_minutes = _parse_time_to_minutes(commuter.departure_time)
    if "deadline_arrival" not in values:
        commuter.deadline_arrival = _minutes_to_time_str(
            dep_minutes + commuter.normal_duration_min + commuter.arrival_buffer_min)
    if "proactive_check_time" not in values or ("departure_time" in explicit and "proactive_check_time" not in explicit):
        commuter.proactive_check_time = _minutes_to_time_str(dep_minutes - commuter.proactive_lead_min)
    if router_instance is None:
        from ..routing.multimodal_router import MultimodalRouter
        router_instance = MultimodalRouter()
    route = router_instance.route_arbitrary_commute(
        origin_station=commuter.boarding_station, dest_station=commuter.alighting_station, rain_active=rain_active)
    if not route:
        return {"status": "error", "code": "NO_ROUTE", "message": "No route found for the requested journey"}
    candidates = [_adapt_route(candidate, commuter, rain_active, dep_minutes)
                  for candidate in [route, *route.get("alternatives", [])]]
    feasible = [candidate for candidate in candidates if not candidate["constraint_violations"]]
    if not feasible:
        return {"status": "error", "code": "NO_FEASIBLE_ROUTE", "profile": commuter.to_dict(),
                "message": "Available routes could not satisfy the required constraints", "candidate_routes": candidates}
    feasible.sort(key=lambda candidate: _route_score(candidate, commuter, rain_active))
    selected = feasible[0]
    delay = selected.get("delay_minutes", 0)
    deadline_minutes = _parse_time_to_minutes(commuter.deadline_arrival)
    if deadline_minutes < dep_minutes:
        deadline_minutes += 1440
    arrival_minutes = dep_minutes + selected["total_duration_min"]
    noise_eval = evaluate_noise_filter(delay, commuter.delay_threshold_min,
                                      selected["estimated_arrival"], commuter.deadline_arrival)
    if arrival_minutes > deadline_minutes:
        noise_eval.update(urgency="CRITICAL", status_color="rose", is_delayed=True,
                          notification_action="PROACTIVE_PUSH_FIRED", reason="Arrival exceeds the requested deadline.")
    elif noise_eval["is_delayed"] and delay < commuter.delay_threshold_min:
        noise_eval.update(urgency="CALM", status_color="emerald", is_delayed=False,
                          notification_action="SUPPRESSED", reason="Arrival is within the requested deadline.")
    from ..routing.graph_router import MRT_LINES
    lines = selected.get("lines_used", [selected.get("line", "MRT")])
    codes = [station["code"] for line in lines for station in MRT_LINES.get(line, [])
             if station["name"] == commuter.boarding_station]
    crowd_eval = evaluate_pcd_forecast(
        forecast_data=pcd_forecast_data if commuter.crowd_tolerance != "high" and commuter.crowd_advance_lead_min > 0 else None,
        station_code=codes[0] if codes else commuter.boarding_station,
        station_name=commuter.boarding_station, departure_time=commuter.departure_time,
        advance_lead_min=0 if commuter.crowd_tolerance == "high" else commuter.crowd_advance_lead_min)
    advice = synthesize_actionable_advice(
        is_delayed=noise_eval["is_delayed"], delay_minutes=delay,
        ewl_arrival=selected["estimated_arrival"], dtl_arrival=selected["estimated_arrival"],
        raw_notice_text=raw_notice_text, target_arrival=commuter.deadline_arrival,
        persona_id=commuter.id, profile=commuter.to_dict(), route=selected,
        alternatives=feasible[1:], pcd_forecast_advice=crowd_eval.get("advice") if crowd_eval["forecast_detected"] else None)
    profile_dict = commuter.to_dict()
    if commuter.id not in ALL_PERSONAS:
        profile_dict = register_custom_persona(profile_dict)
    if activate_profile:
        set_active_persona(commuter.id)
    return {
        "status": "success", "profile": profile_dict, "persona_id": commuter.id, "route": selected,
        "routes": {"primary_custom": selected, "arbitrary_route": selected, "primary_ewl": selected},
        "alternative_routes": feasible[1:],
        "decision": {**noise_eval, "delay_minutes": delay, "threshold_minutes": commuter.delay_threshold_min,
                     "headline": advice["headline"], "one_line_advice": advice["one_line_advice"],
                     "active_recommendation": advice["active_recommendation"], "ai_metadata": advice.get("ai_metadata", {})},
        "pcd_forecast": crowd_eval,
        "weather": {"summary": weather_summary or ("Rain active along corridor." if rain_active else "Clear weather."),
                    "rain_alert": rain_active},
    }
