"""
PS2: Smart Commuter Companion Web Application.
Main Flask server providing REST API and mobile-optimized frontend.
"""

import os
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

from flask import Flask, render_template, jsonify, request
from src.engine import CommuterEngine, RACHEL_PROFILE
from src.scenarios import list_scenarios, SCENARIO_NORMAL
from src.canonical_lines import LINE_COLORS
from src.routing.multimodal_router import MultimodalRouter
from src.routing.location_resolver import suggest_locations

app = Flask(__name__, static_folder="static", template_folder="templates")
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


def _enrich_evaluation_with_custom_route(evaluation, origin, dest, rain_active=False):
    """
    If origin or destination are customized (not the default Tampines/Raffles Place corridor),
    replaces Rachel's hardcoded corridor with the door-to-door calculated route and
    generates custom map layers for Leaflet rendering.
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
    first_stn_meta = get_station_metadata(orig_res.get("station", ""))
    last_stn_meta = get_station_metadata(dest_res.get("station", ""))
    first_stn_coord = first_stn_meta["coords"] if first_stn_meta else orig_coords
    last_stn_coord = last_stn_meta["coords"] if last_stn_meta else dest_coords

    if not orig_coords and first_stn_coord:
        orig_coords = first_stn_coord
    if not dest_coords and last_stn_coord:
        dest_coords = last_stn_coord

    walking_legs = {}
    if orig_coords and first_stn_coord:
        walking_legs["origin_walk"] = {
            "name": f"Walk from {orig_res.get('display')} to {orig_res.get('station')} MRT",
            "coords": [orig_coords, first_stn_coord]
        }
    if last_stn_coord and dest_coords:
        walking_legs["dest_walk"] = {
            "name": f"Walk from {dest_res.get('station')} MRT to {dest_res.get('display')}",
            "coords": [last_stn_coord, dest_coords]
        }

    # Station coordinates along path
    segments = route_res.get("path_segments", [])
    custom_stations = []
    custom_track = []
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

    primary_line = route_res.get("line", "DTL")
    track_color = LINE_COLORS.get(primary_line, "#2563eb")

    evaluation["is_custom"] = True
    evaluation["routes"]["primary_ewl"] = {
        "id": "primary_ewl",
        "title": route_res["title"],
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
        "legs": route_res["legs"]
    }

    lines_str = " -> ".join(route_res.get("lines_used", []))
    evaluation["decision"]["headline"] = f"Route: {orig_res.get('display')} to {dest_res.get('display')}"
    evaluation["decision"]["one_line_advice"] = f"Via {lines_str} ({route_res.get('status')}). Travel time: {route_res.get('total_duration_min')} mins."
    evaluation["decision"]["is_delayed"] = False
    evaluation["decision"]["urgency"] = "CALM"

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
        "custom_stations": custom_stations,
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
    rain_active = request.args.get("rain", "0") == "1"
    evaluation = engine.evaluate_commute(custom_arrival=arrival_time, custom_origin=origin, custom_dest=dest)
    evaluation = _enrich_evaluation_with_custom_route(evaluation, origin, dest, rain_active=rain_active)
    return jsonify(evaluation)


@app.route("/api/scenarios", methods=["GET"])
def get_scenarios():
    """Returns list of simulation scenarios for judges."""
    return jsonify({
        "current": engine.current_scenario_id,
        "scenarios": list_scenarios()
    })


@app.route("/api/scenario/select", methods=["POST"])
def select_scenario():
    """Switches active scenario (normal, ewl_fault, weather_surge, live)."""
    data = request.get_json() or {}
    scenario_id = data.get("scenario_id", SCENARIO_NORMAL)
    arrival_time = data.get("arrival_time")
    success = engine.set_scenario(scenario_id)
    if success:
        return jsonify({
            "status": "success",
            "scenario_id": scenario_id,
            "data": engine.evaluate_commute(custom_arrival=arrival_time)
        })
    return jsonify({"status": "error", "message": f"Scenario {scenario_id} not found"}), 400


@app.route("/api/settings", methods=["POST"])
def update_settings():
    """Allows adjusting arrival timing, origin/destination, and delay thresholds."""
    data = request.get_json() or {}
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
    app.run(host="0.0.0.0", port=port, debug=True)

