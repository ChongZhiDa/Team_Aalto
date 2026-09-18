"""
Flask REST API Adapter for Customizable Commuter Profiles & Routing.
Connects frontend UI and client requests to create_custom_user_route()
and persona persistence.
"""

import os
from typing import Any, Dict
from flask import Blueprint, request, jsonify

from .custom_router import create_custom_user_route
from .personas import (
    list_personas,
    get_persona,
    register_custom_persona,
    update_persona,
    save_personas,
    load_personas,
    get_active_persona,
    set_active_persona,
)

custom_route_bp = Blueprint("custom_route_bp", __name__)


@custom_route_bp.route("/api/custom/personas", methods=["GET"])
def api_list_custom_personas():
    """Returns all registered personas and the current active persona."""
    try:
        personas = list_personas()
        active = get_active_persona()
        return jsonify({
            "status": "success",
            "personas": personas,
            "current": active.get("id") if active else "rachel"
        })
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


@custom_route_bp.route("/api/custom/personas", methods=["POST"])
def api_register_persona():
    """Registers a new custom persona."""
    data = request.get_json() or {}
    try:
        profile = register_custom_persona(data)
        return jsonify({
            "status": "success",
            "profile": profile
        }), 201
    except ValueError as e:
        return jsonify({
            "status": "error",
            "code": "INVALID_PROFILE",
            "message": str(e)
        }), 400
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


@custom_route_bp.route("/api/custom/personas/<persona_id>", methods=["PUT", "PATCH"])
def api_update_persona(persona_id: str):
    """Updates an existing persona by ID."""
    data = request.get_json() or {}
    try:
        profile = update_persona(persona_id, data)
        return jsonify({
            "status": "success",
            "profile": profile
        })
    except KeyError as e:
        return jsonify({
            "status": "error",
            "code": "NOT_FOUND",
            "message": f"Persona {persona_id} not found"
        }), 404
    except ValueError as e:
        return jsonify({
            "status": "error",
            "code": "INVALID_UPDATE",
            "message": str(e)
        }), 400
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


@custom_route_bp.route("/api/custom/personas/save", methods=["POST"])
def api_save_personas():
    """Saves registered personas to a specified or default JSON file."""
    data = request.get_json() or {}
    filepath = data.get("filepath", "data/custom_personas.json")
    try:
        dir_name = os.path.dirname(filepath)
        if dir_name:
            os.makedirs(dir_name, exist_ok=True)
        save_personas(filepath)
        return jsonify({
            "status": "success",
            "filepath": filepath,
            "message": f"Personas saved successfully to {filepath}"
        })
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


@custom_route_bp.route("/api/custom/personas/load", methods=["POST"])
def api_load_personas():
    """Loads personas from a specified or default JSON file."""
    data = request.get_json() or {}
    filepath = data.get("filepath", "data/custom_personas.json")
    if not os.path.exists(filepath):
        return jsonify({
            "status": "error",
            "code": "FILE_NOT_FOUND",
            "message": f"File '{filepath}' does not exist"
        }), 404
    try:
        loaded = load_personas(filepath)
        return jsonify({
            "status": "success",
            "loaded_count": len(loaded),
            "personas": list_personas()
        })
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


@custom_route_bp.route("/api/custom/route", methods=["POST"])
def api_custom_user_route():
    """
    Executes profile-driven journey calculation using create_custom_user_route().
    Accepts persona ID, overrides, locations, and constraint parameters.
    """
    data = request.get_json() or {}

    persona_id = data.get("persona_id") or data.get("id")
    profile = None
    if persona_id:
        profile = get_persona(persona_id)

    # Extract explicit journey overrides
    origin = data.get("origin")
    destination = data.get("destination")
    name = data.get("name")
    departure_time = data.get("departure_time")
    deadline_arrival = data.get("deadline_arrival")
    delay_threshold_min = data.get("delay_threshold_min")
    if delay_threshold_min is not None:
        try:
            delay_threshold_min = int(delay_threshold_min)
        except (ValueError, TypeError):
            pass

    cycling_enabled = data.get("cycling_enabled")
    stair_aversion = data.get("stair_aversion")
    rain_active = bool(data.get("rain_active", False))
    activate_profile = bool(data.get("activate_profile", False))

    # Collect additional profile override keys
    known_keys = {
        "persona_id", "id", "origin", "destination", "name",
        "departure_time", "deadline_arrival", "delay_threshold_min",
        "cycling_enabled", "stair_aversion", "rain_active", "activate_profile"
    }
    overrides: Dict[str, Any] = {k: v for k, v in data.items() if k not in known_keys}

    try:
        result = create_custom_user_route(
            origin=origin,
            destination=destination,
            name=name,
            departure_time=departure_time,
            deadline_arrival=deadline_arrival,
            delay_threshold_min=delay_threshold_min,
            cycling_enabled=cycling_enabled,
            stair_aversion=stair_aversion,
            rain_active=rain_active,
            profile=profile,
            activate_profile=activate_profile,
            **overrides
        )

        if result.get("status") == "success":
            return jsonify(result), 200
        else:
            # Domain error like UNKNOWN_STATION, NO_ROUTE, NO_FEASIBLE_ROUTE
            code = result.get("code", "ERROR")
            http_status = 400
            if code == "UNKNOWN_STATION":
                http_status = 404
            elif code == "NO_ROUTE":
                http_status = 404
            elif code == "NO_FEASIBLE_ROUTE":
                http_status = 422
            return jsonify(result), http_status

    except ValueError as e:
        return jsonify({
            "status": "error",
            "code": "VALIDATION_ERROR",
            "message": str(e)
        }), 400
    except Exception as e:
        return jsonify({
            "status": "error",
            "code": "INTERNAL_ERROR",
            "message": str(e)
        }), 500


def register_custom_route_adapter(app):
    """Utility to register the custom route blueprint onto the main Flask app."""
    app.register_blueprint(custom_route_bp)
