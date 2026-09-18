"""
Commuter Persona profiles and behavioral constraints.
Defines Rachel, Arjun, and Mdm Lim.
"""

from typing import Dict, Any

RACHEL_PROFILE: Dict[str, Any] = {
    "id": "rachel",
    "name": "Rachel",
    "persona": "Fixed-Schedule Corporate Commuter",
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
}

ARJUN_PROFILE: Dict[str, Any] = {
    "id": "arjun",
    "name": "Arjun",
    "persona": "Multi-Modal, Flexible-Start Worker",
    "origin": "Punggol Field",
    "destination": "one-north (Fusionopolis)",
    "departure_time": "08:15 AM",
    "proactive_check_time": "07:45 AM",
    "deadline_arrival": "09:30 AM",
    "delay_threshold_min": 25,
    "stair_aversion": False,
    "cycling_enabled": True,
}

MDM_LIM_PROFILE: Dict[str, Any] = {
    "id": "mdm_lim",
    "name": "Mdm Lim",
    "persona": "Accessibility-Constrained Occasional Traveller",
    "origin": "Bedok North Ave 3",
    "destination": "Singapore General Hospital (Outram Park)",
    "departure_time": "09:15 AM",
    "proactive_check_time": "08:00 AM",
    "deadline_arrival": "10:30 AM",
    "delay_threshold_min": 10,
    "stair_aversion": True,
    "cycling_enabled": False,
}

ALL_PERSONAS = {
    "rachel": RACHEL_PROFILE,
    "arjun": ARJUN_PROFILE,
    "mdm_lim": MDM_LIM_PROFILE,
}


def get_persona(persona_id: str) -> Dict[str, Any]:
    return ALL_PERSONAS.get(persona_id, RACHEL_PROFILE)

