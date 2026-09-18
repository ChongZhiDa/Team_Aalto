"""
Commuter Persona profiles and behavioral constraints.
Defines Rachel, Arjun, and Mdm Lim.
"""

from typing import Dict, Any, List, Optional

RACHEL_PROFILE: Dict[str, Any] = {
    "id": "rachel",
    "name": "Rachel",
    "persona": "Fixed-Schedule Corporate Commuter",
    "tag": "EWL Direct Corridor",
    "origin": "Blk 230 Tampines St 21",
    "destination": "One Raffles Place, CBD",
    "departure_time": "07:40 AM",
    "proactive_check_time": "07:20 AM",
    "deadline_arrival": "08:45 AM",
    "meeting_time": "09:00 AM",
    "normal_duration_min": 42,
    "delay_threshold_min": 15,
    "stair_aversion": False,
    "cycling_enabled": False,
    "walking_speed_mps": 1.35,
    "primary_line": "EWL",
    "boarding_station": "EW2",
    "alighting_station": "EW14",
}

ARJUN_PROFILE: Dict[str, Any] = {
    "id": "arjun",
    "name": "Arjun",
    "persona": "Multi-Modal, Flexible-Start Worker",
    "tag": "Cycle + NEL/CCL",
    "origin": "Punggol Field",
    "destination": "one-north (Fusionopolis)",
    "departure_time": "08:15 AM",
    "proactive_check_time": "07:45 AM",
    "deadline_arrival": "09:30 AM",
    "meeting_time": "10:00 AM",
    "normal_duration_min": 44,
    "delay_threshold_min": 25,
    "stair_aversion": False,
    "cycling_enabled": True,
    "walking_speed_mps": 1.40,
    "cycling_speed_mps": 4.0,
    "primary_line": "NEL",
    "boarding_station": "NE17",
    "transfer_station": "CC13",
    "alighting_station": "CC23",
}

MDM_LIM_PROFILE: Dict[str, Any] = {
    "id": "mdm_lim",
    "name": "Mdm Lim",
    "persona": "Accessibility-Constrained Occasional Traveller",
    "tag": "Step-Free / Lift Priority",
    "origin": "Bedok North Ave 3",
    "destination": "Singapore General Hospital (Outram Park)",
    "departure_time": "09:15 AM",
    "proactive_check_time": "08:00 AM",
    "deadline_arrival": "10:30 AM",
    "meeting_time": "10:45 AM",
    "normal_duration_min": 43,
    "delay_threshold_min": 10,
    "stair_aversion": True,
    "cycling_enabled": False,
    "walking_speed_mps": 0.85,
    "requires_step_free": True,
    "requires_lift_monitoring": True,
    "primary_line": "EWL",
    "boarding_station": "EW9",
    "alighting_station": "EW16",
}

ALL_PERSONAS: Dict[str, Dict[str, Any]] = {
    "rachel": RACHEL_PROFILE,
    "arjun": ARJUN_PROFILE,
    "mdm_lim": MDM_LIM_PROFILE,
}

_CURRENT_ACTIVE_PERSONA_ID: str = "rachel"


def get_persona(persona_id: str) -> Dict[str, Any]:
    """Retrieves persona profile dictionary by ID, defaulting to Rachel."""
    clean_id = str(persona_id).strip().lower()
    return ALL_PERSONAS.get(clean_id, RACHEL_PROFILE)


def list_personas() -> List[Dict[str, Any]]:
    """Returns list of all available persona profiles for selection."""
    return [
        {
            "id": p["id"],
            "name": p["name"],
            "persona": p["persona"],
            "tag": p.get("tag", ""),
            "origin": p["origin"],
            "destination": p["destination"],
            "departure_time": p["departure_time"],
            "deadline_arrival": p["deadline_arrival"],
            "delay_threshold_min": p["delay_threshold_min"],
            "cycling_enabled": p.get("cycling_enabled", False),
            "stair_aversion": p.get("stair_aversion", False),
        }
        for p in ALL_PERSONAS.values()
    ]


def set_active_persona(persona_id: str) -> bool:
    """Sets the globally active persona ID if valid."""
    global _CURRENT_ACTIVE_PERSONA_ID
    clean_id = str(persona_id).strip().lower()
    if clean_id in ALL_PERSONAS:
        _CURRENT_ACTIVE_PERSONA_ID = clean_id
        return True
    return False


def get_active_persona() -> Dict[str, Any]:
    """Returns the currently active persona profile."""
    return ALL_PERSONAS.get(_CURRENT_ACTIVE_PERSONA_ID, RACHEL_PROFILE)
