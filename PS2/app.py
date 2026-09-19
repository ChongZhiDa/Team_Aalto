"""
PS2: Smart Commuter Companion Web Application.
Main Flask server providing REST API and mobile-optimized frontend.
"""

import os
from datetime import datetime, timedelta
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

from flask import Flask, render_template, jsonify, request
from src.engine import CommuterEngine, RACHEL_PROFILE
from src.scenarios import list_scenarios, get_scenario, SCENARIO_NORMAL
from src.canonical_lines import LINE_COLORS
from src.routing.multimodal_router import MultimodalRouter
from src.routing.location_resolver import suggest_locations
from src.intelligence.custom_route_adapter import register_custom_route_adapter
from src.intelligence.personas import get_persona

app = Flask(__name__, static_folder="static", template_folder="templates")
register_custom_route_adapter(app)
engine = CommuterEngine()
_router = MultimodalRouter()


@app.route("/api/suggest", methods=["GET"])
def get_suggestions():
    """
    Returns autocomplete suggestions as user types an address, postal code,
    landmark, or station.
    Query params: q=<text>
    """
    q = (request.args.get("q") or "").strip()
    if not q:
        return jsonify([])
    stn_names = _router.graph_router.get_all_station_names()
    suggestions = suggest_locations(q, station_names=stn_names)
    return jsonify(suggestions)


@app.route("/api/route", methods=["GET"])
def get_arbitrary_route():
    """
    Fuzzy door-to-door routing for any origin/destination text.
    Resolves landmarks, malls, hospitals, MRT station names (with/without 'MRT') etc.
    Query params: origin=<text>&destination=<text>&rain=<0|1>
    """
    origin = (request.args.get("origin") or "").strip()
    dest = (request.args.get("destination") or "").strip()
    rain_active = request.args.get("rain", "0") == "1"

    if not origin or not dest:
        return jsonify({"error": "origin and destination are required"}), 400

    result = _router.route_door_to_door(origin, dest, rain_active=rain_active)
    if result.get("error"):
        return jsonify(result), 404

    return jsonify(result)


@app.route("/")
def index():
    """Serves the mobile-first companion interface."""
    return render_template("index.html")


LINE_COLORS = {
    "EWL": "#10b981",  # Emerald
    "DTL": "#2563eb",  # Blue
    "NEL": "#8b5cf6",  # Purple
    "CCL": "#f59e0b",  # Amber / Orange
    "NSL": "#ef4444",  # Red
    "TEL": "#92400e",  # Brown
    "MRT": "#2563eb",
}


def _enrich_evaluation_with_custom_route(evaluation, origin, dest, rain_active=False):
    """
    If origin or destination are customized (not the default Tampines/Raffles Place corridor),
    replaces Rachel's hardcoded corridor with the door-to-door calculated route and
    generates custom map layers for Leaflet rendering with real pedestrian footpaths.
    """
    if not origin or not dest:
        return evaluation

    orig_str = str(origin).strip()
    dest_str = str(dest).strip()

    # Check if this is a custom route rather than Rachel's default Tampines -> Raffles corridor
    is_custom = bool("tampines" not in orig_str.lower() or "raffles" not in dest_str.lower())
    if not is_custom:
        return evaluation

    route_res = _router.route_door_to_door(orig_str, dest_str, rain_active=rain_active)
    if not route_res or route_res.get("error"):
        return evaluation

    orig_res = route_res.get("origin_resolved", {})
    dest_res = route_res.get("dest_resolved", {})
    orig_coords = orig_res.get("coordinates")
    dest_coords = dest_res.get("coordinates")

    from src.routing.geojson_loader import get_station_metadata
    from src.routing.location_resolver import get_pedestrian_path

    first_stn_meta = get_station_metadata(orig_res.get("station", ""))
    last_stn_meta = get_station_metadata(dest_res.get("station", ""))
    first_stn_coord = first_stn_meta["coords"] if first_stn_meta else orig_coords
    last_stn_coord = last_stn_meta["coords"] if last_stn_meta else dest_coords

    if not orig_coords and first_stn_coord:
        orig_coords = first_stn_coord
    if not dest_coords and last_stn_coord:
        dest_coords = last_stn_coord

    # Real turn-by-turn pedestrian walking footpaths avoiding buildings
    walking_legs = {}
    if orig_coords and first_stn_coord:
        origin_path, origin_dist = get_pedestrian_path(orig_coords, first_stn_coord)
        walking_legs["origin_walk"] = {
            "name": f"Walk from {orig_res.get('display')} to {orig_res.get('station')} MRT",
            "coords": origin_path,
            "distance_m": origin_dist,
        }
    if last_stn_coord and dest_coords:
        dest_path, dest_dist = get_pedestrian_path(last_stn_coord, dest_coords)
        walking_legs["dest_walk"] = {
            "name": f"Walk from {dest_res.get('station')} MRT to {dest_res.get('display')}",
            "coords": dest_path,
            "distance_m": dest_dist,
        }

    # Station coordinates along path
    segments = route_res.get("path_segments", [])
    custom_stations = []
    custom_track = []
    custom_tracks = []
    seen_stns = set()

    for seg in segments:
        for sname in [seg.get("from_station", ""), seg.get("to_station", "")]:
            if sname and sname.lower() not in seen_stns:
                seen_stns.add(sname.lower())
                smeta = get_station_metadata(sname)
                if smeta:
                    custom_stations.append({
                        "name": smeta["name"],
                        "coords": smeta["coords"],
                        "line": seg.get("line", "MRT"),
                        "code": seg.get("line", "MRT")
                    })
                    custom_track.append(smeta["coords"])

    # Group transit segments by MRT line for multi-color rail tracks
    curr_track = None
    for seg in segments:
        m1 = get_station_metadata(seg.get("from_station", ""))
        m2 = get_station_metadata(seg.get("to_station", ""))
        if not m1 or not m2:
            continue
        line_code = seg.get("line", "MRT")
        color = LINE_COLORS.get(line_code, "#2563eb")
        if not curr_track or curr_track["line"] != line_code:
            if curr_track:
                custom_tracks.append(curr_track)
            curr_track = {
                "line": line_code,
                "color": color,
                "coords": [m1["coords"], m2["coords"]]
            }
        else:
            curr_track["coords"].append(m2["coords"])
    if curr_track:
        custom_tracks.append(curr_track)

    primary_line = route_res.get("line", "DTL")
    track_color = LINE_COLORS.get(primary_line, "#2563eb")

    prim_lines = " -> ".join(route_res.get("lines_used", []))
    prim_title = route_res["title"]
    if prim_lines:
        prim_title = f"{prim_title} (via {prim_lines})"

    # Keep the map's custom geometry, but let the UI render the searched route
    # alongside its dynamic alternatives instead of collapsing to one card.
    evaluation["is_custom"] = False
    evaluation["is_searched_route"] = True
    evaluation["routes"]["primary_ewl"] = {
        "id": "primary_ewl",
        "title": prim_title,
        "transit_type": route_res["transit_type"],
        "line": route_res["line"],
        "lines_used": route_res["lines_used"],
        "total_duration_min": route_res["total_duration_min"],
        "estimated_arrival": route_res["estimated_arrival"],
        "delay_minutes": 0,
        "status": route_res["status"],
        "crowd_level": "m",
        "is_recommended": True,
        "sheltered_percent": route_res.get("sheltered_percent", 75),
        "legs": route_res["legs"],
        "polyline": route_res.get("polyline", []),
        "stations": route_res.get("stations", []),
        "walking_paths": route_res.get("walking_paths", {}),
    }
    evaluation["routes"]["arbitrary_route"] = evaluation["routes"]["primary_ewl"]

    # Populate dynamic alternative route if available
    alternatives = route_res.get("alternatives", [])
    if alternatives:
        alt_route = alternatives[0]
        alt_line = alt_route.get("line", "MRT")
        alt_lines = " -> ".join(alt_route.get("lines_used", []))
        alt_title = f"Alternative: {alt_lines}" if alt_lines else alt_route["title"]
        alt_track_color = LINE_COLORS.get(alt_line, "#6366f1")
        evaluation["routes"]["bypass_dtl"] = {
            "id": "bypass_dtl",
            "title": alt_title,
            "transit_type": alt_route["transit_type"],
            "line": alt_route["line"],
            "lines_used": alt_route["lines_used"],
            "total_duration_min": alt_route["total_duration_min"],
            "estimated_arrival": alt_route["estimated_arrival"],
            "delay_minutes": 0,
            "status": alt_route["status"],
            "crowd_level": "l",
            "is_recommended": False,
            "sheltered_percent": alt_route.get("sheltered_percent", 80),
            "legs": alt_route["legs"],
            "polyline": alt_route.get("polyline", []),
            "stations": alt_route.get("stations", []),
            "walking_paths": alt_route.get("walking_paths", {}),
        }
    else:
        evaluation["routes"].pop("bypass_dtl", None)

    # Include public bus alternative for any location (Item 3: include bus lines for routing)
    bus_route = _router.compute_custom_bus_journey(
        orig_coords=orig_coords,
        dest_coords=dest_coords,
        orig_display=orig_res.get("display", orig_str),
        dest_display=dest_res.get("display", dest_str),
        rain_active=rain_active,
    )
    if bus_route:
        evaluation["routes"]["bypass_bus10e"] = bus_route

    lines_str = " -> ".join(route_res.get("lines_used", []))
    scenario_delay = evaluation["decision"].get("delay_minutes", 0)
    evaluation["decision"]["headline"] = f"Route: {orig_res.get('display')} to {dest_res.get('display')}"
    scenario_note = f" Scenario add-on: +{scenario_delay} min." if scenario_delay else ""
    evaluation["decision"]["one_line_advice"] = (
        f"Via {lines_str} ({route_res.get('status')}). "
        f"Travel time: {route_res.get('total_duration_min')} mins.{scenario_note}"
    )
    if alternatives:
        evaluation["decision"]["active_recommendation"] = f"Alternative via {' -> '.join(alternatives[0].get('lines_used', []))}"

    alt_track = alternatives[0].get("polyline", []) if alternatives else []
    alt_stations = alternatives[0].get("stations", []) if alternatives else []
    bus_track = bus_route.get("polyline", []) if bus_route else []

    evaluation["map_layers"] = {
        "is_custom": True,
        "origin": {
            "name": orig_res.get("display", orig_str),
            "coords": orig_coords
        },
        "destination": {
            "name": dest_res.get("display", dest_str),
            "coords": dest_coords
        },
        "walking_legs": walking_legs,
        "custom_track": custom_track,
        "custom_tracks": custom_tracks,
        "custom_stations": custom_stations,
        "alt_track": alt_track,
        "alt_stations": alt_stations,
        "bus10e_track": bus_track,
        "bus_title": bus_route.get("title", "Public Bus Service") if bus_route else "Public Bus",
        "track_color": track_color,
        "route_summary": route_res.get("status", ""),
        "ewl_stations": [],
        "dtl_stations": [],
        "ewl_track": [],
        "dtl_track": [],
    }
    return evaluation


@app.route("/api/status", methods=["GET"])
def get_commute_status():
    """Returns current proactive status, noise filter decisions, and route coordinates."""
    arrival_time = request.args.get("arrival_time")
    origin = request.args.get("origin")
    dest = request.args.get("destination")
    persona = request.args.get("persona")
    rain_active = request.args.get("rain", "0") == "1"
    evaluation = engine.evaluate_commute(
        custom_arrival=arrival_time,
        custom_origin=origin,
        custom_dest=dest,
        custom_persona=persona
    )
    evaluation = _enrich_evaluation_with_custom_route(evaluation, origin, dest, rain_active=rain_active)
    return jsonify(evaluation)


@app.route("/api/scenarios", methods=["GET"])
def get_scenarios():
    """Returns list of simulation scenarios for judges."""
    return jsonify({
        "current": engine.current_scenario_id,
        "scenarios": list_scenarios()
    })


@app.route("/api/custom/notifications/next-day", methods=["GET"])
def get_next_day_notifications():
    """Evaluate saved commute plans that are scheduled for tomorrow."""
    persona_id = request.args.get("persona_id", "rachel")
    profile = get_persona(persona_id)
    simulated_date = request.args.get("date")
    try:
        base_date = datetime.strptime(simulated_date, "%Y-%m-%d") if simulated_date else datetime.now()
    except ValueError:
        base_date = datetime.now()
    tomorrow = base_date + timedelta(days=1)
    day_code = tomorrow.strftime("%a").lower()[:3]
    notifications = []
    scenario = get_scenario(engine.current_scenario_id)
    disrupted_line = scenario.get("disrupted_line") if scenario else None
    whole_line_failure = bool(scenario and scenario.get("whole_line_failure"))

    def time_to_minutes(value):
        parsed = datetime.strptime(str(value).strip().upper(), "%H:%M") if len(str(value).strip()) == 5 else datetime.strptime(str(value).strip().upper(), "%I:%M %p")
        return parsed.hour * 60 + parsed.minute

    def minutes_to_time(value):
        value %= 1440
        return datetime(2000, 1, 1, value // 60, value % 60).strftime("%I:%M %p")

    for plan in profile.get("scheduled_routes", []):
        plan_days = [str(day).lower()[:3] for day in plan.get("days", [])]
        if not plan.get("enabled", True) or day_code not in plan_days:
            continue
        evaluation = engine.evaluate_commute(
            custom_arrival=plan.get("arrival_time"),
            custom_origin=plan.get("origin"),
            custom_dest=plan.get("destination"),
            custom_persona=persona_id,
        )
        evaluation = _enrich_evaluation_with_custom_route(
            evaluation, plan.get("origin"), plan.get("destination")
        )
        decision = evaluation.get("decision", {})
        affected_route = _router.route_door_to_door(plan.get("origin"), plan.get("destination"))
        route_lines = set(affected_route.get("lines_used", [])) if affected_route else set()
        route_affected = not whole_line_failure or not disrupted_line or disrupted_line in route_lines
        if route_affected and (decision.get("is_delayed") or decision.get("notification_action") == "PROACTIVE_PUSH_FIRED"):
            arrival_minutes = time_to_minutes(plan.get("arrival_time", "08:45"))
            replacement_route = _router.route_door_to_door(
                plan.get("origin"), plan.get("destination"), disrupted_line=disrupted_line
            ) if disrupted_line else None

            selected_replacement = replacement_route or (affected_route.get("alternatives", [None])[0] if affected_route else None)
            if selected_replacement:
                replacement_duration = int(selected_replacement.get("total_duration_min", 0))
                selected_replacement = {**selected_replacement,
                    "departure_time": minutes_to_time(arrival_minutes - replacement_duration),
                    "estimated_arrival": minutes_to_time(arrival_minutes)}
            notifications.append({
                "plan_id": plan.get("id"),
                "label": plan.get("label") or f"{plan.get('origin')} to {plan.get('destination')}",
                "origin": plan.get("origin"),
                "destination": plan.get("destination"),
                "arrival_time": plan.get("arrival_time"),
                "headline": decision.get("headline"),
                "advice": decision.get("one_line_advice"),
                "delay_minutes": decision.get("delay_minutes", 0),
                "notification_action": decision.get("notification_action"),
                "affected_route": {
                    "title": affected_route.get("title") if affected_route else "Current scheduled route",
                    "duration_min": affected_route.get("total_duration_min") if affected_route else None,
                    "lines_used": affected_route.get("lines_used", []) if affected_route else [],
                },
                "replacement_route": selected_replacement,
                "replacement_departure": selected_replacement.get("departure_time") if selected_replacement else None,
                "replacement_arrival": selected_replacement.get("estimated_arrival") if selected_replacement else None,
                "whole_line_failure": whole_line_failure,
                "disrupted_line": disrupted_line,
            })

    return jsonify({
        "status": "success",
        "date": tomorrow.strftime("%Y-%m-%d"),
        "day": day_code,
        "notifications": notifications,
    })


@app.route("/api/scenario/select", methods=["POST"])
def select_scenario():
    """Switches active scenario (normal, ewl_fault, weather_surge, live)."""
    data = request.get_json() or {}
    scenario_id = data.get("scenario_id", SCENARIO_NORMAL)
    arrival_time = data.get("arrival_time")
    origin = data.get("origin")
    destination = data.get("destination")
    success = engine.set_scenario(scenario_id)
    if success:
        evaluation = engine.evaluate_commute(
            custom_arrival=arrival_time,
            custom_origin=origin,
            custom_dest=destination,
        )
        evaluation = _enrich_evaluation_with_custom_route(
            evaluation,
            origin,
            destination,
            rain_active=bool(evaluation.get("weather", {}).get("rain_alert")),
        )
        return jsonify({
            "status": "success",
            "scenario_id": scenario_id,
            "data": evaluation,
        })
    return jsonify({"status": "error", "message": f"Scenario {scenario_id} not found"}), 400


@app.route("/api/personas", methods=["GET"])
def get_personas():
    """Returns list of commuter personas (Rachel, Arjun, Mdm Lim)."""
    return jsonify({
        "current": engine.current_persona_id,
        "personas": engine.list_personas()
    })


@app.route("/api/persona/select", methods=["POST"])
def select_persona():
    """Switches active persona (rachel, arjun, mdm_lim)."""
    data = request.get_json() or {}
    persona_id = data.get("persona_id", "rachel")
    success = engine.set_persona(persona_id)
    if success:
        return jsonify({
            "status": "success",
            "persona_id": persona_id,
            "data": engine.evaluate_commute()
        })
    return jsonify({"status": "error", "message": f"Persona {persona_id} not found"}), 400


@app.route("/api/custom-route", methods=["POST"])
@app.route("/api/persona/custom", methods=["POST"])
def create_custom_route():
    """
    Creates an on-the-spot customized route and persona for a new user.
    Accepts arbitrary origin, destination, departure time, arrival deadline,
    delay threshold, and cycling/stair constraints.
    """
    data = request.get_json() or {}
    evaluation = engine.create_custom_commute(data)
    return jsonify({
        "status": "success",
        "persona_id": engine.current_persona_id,
        "data": evaluation
    })


@app.route("/api/settings", methods=["POST"])
def update_settings():
    """Allows adjusting arrival timing, origin/destination, delay thresholds, and persona."""
    data = request.get_json() or {}
    if "persona_id" in data:
        engine.set_persona(data["persona_id"])
    if "delay_threshold_min" in data:
        RACHEL_PROFILE["delay_threshold_min"] = int(data["delay_threshold_min"])
    if "deadline_arrival" in data:
        RACHEL_PROFILE["deadline_arrival"] = str(data["deadline_arrival"])
    if "origin" in data:
        RACHEL_PROFILE["origin"] = str(data["origin"])
    if "destination" in data:
        RACHEL_PROFILE["destination"] = str(data["destination"])

    arrival_time = data.get("arrival_time") or RACHEL_PROFILE.get("deadline_arrival")
    origin = data.get("origin") or RACHEL_PROFILE.get("origin")
    dest = data.get("destination") or RACHEL_PROFILE.get("destination")
    eval_data = engine.evaluate_commute(custom_arrival=arrival_time, custom_origin=origin, custom_dest=dest)
    eval_data = _enrich_evaluation_with_custom_route(eval_data, origin, dest)
    return jsonify({
        "status": "success",
        "profile": RACHEL_PROFILE,
        "data": eval_data
    })


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    print(f"Starting Smart Commuter Companion on http://localhost:{port}")
    app.run(host="0.0.0.0", port=port, debug=False)

