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

app = Flask(__name__, static_folder="static", template_folder="templates")
engine = CommuterEngine()


@app.route("/")
def index():
    """Serves the mobile-first companion interface."""
    return render_template("index.html")


@app.route("/api/status", methods=["GET"])
def get_commute_status():
    """Returns current proactive status, noise filter decisions, and route coordinates."""
    arrival_time = request.args.get("arrival_time")
    origin = request.args.get("origin")
    dest = request.args.get("destination")
    persona = request.args.get("persona")
    evaluation = engine.evaluate_commute(
        custom_arrival=arrival_time,
        custom_origin=origin,
        custom_dest=dest,
        custom_persona=persona
    )
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
    return jsonify({
        "status": "success",
        "profile": RACHEL_PROFILE,
        "data": engine.evaluate_commute(custom_arrival=arrival_time)
    })


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    print(f"Starting Smart Commuter Companion on http://localhost:{port}")
    app.run(host="0.0.0.0", port=port, debug=True)

