"""
Commuter Persona profiles, behavioral constraints, and dynamic custom router.
Defines canonical personas (Rachel, Arjun, Mdm Lim) and provides
on-the-spot creation of customized commuter profiles and routes for arbitrary users.
"""

from dataclasses import dataclass, field, asdict
from typing import Dict, Any, List, Optional
import re


@dataclass
class CommuterProfile:
    id: str
    name: str
    persona: str
    tag: str = "Custom Route"
    origin: str = "Jurong East"
    destination: str = "Bishan"
    departure_time: str = "08:00 AM"
    proactive_check_time: str = "07:40 AM"
    deadline_arrival: str = "08:50 AM"
    meeting_time: str = "09:00 AM"
    normal_duration_min: int = 35
    delay_threshold_min: int = 15
    stair_aversion: bool = False
    cycling_enabled: bool = False
    walking_speed_mps: float = 1.35
    primary_line: str = "MRT"
    boarding_station: str = "Jurong East"
    alighting_station: str = "Bishan"
    is_custom: bool = True

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'CommuterProfile':
        valid_keys = cls.__dataclass_fields__.keys()
        filtered = {k: v for k, v in data.items() if k in valid_keys}
        return cls(**filtered)


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
    "is_custom": False,
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
    "is_custom": False,
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
    "is_custom": False,
}

ALL_PERSONAS: Dict[str, Dict[str, Any]] = {
    "rachel": RACHEL_PROFILE,
    "arjun": ARJUN_PROFILE,
    "mdm_lim": MDM_LIM_PROFILE,
}

_CURRENT_ACTIVE_PERSONA_ID: str = "rachel"

# Canonical Station Aliases & Landmarks
STATION_ALIASES: Dict[str, str] = {
    "cbd": "Raffles Place",
    "one raffles place": "Raffles Place",
    "raffles": "Raffles Place",
    "sgh": "Outram Park",
    "singapore general hospital": "Outram Park",
    "fusionopolis": "one-north",
    "biopolis": "one-north",
    "nus": "Kent Ridge",
    "ntu": "Pioneer",
    "changi": "Changi Airport",
    "airport": "Changi Airport",
    "tampines st 21": "Tampines",
    "punggol field": "Punggol",
    "bedok north": "Bedok",
    "harbourfront": "HarbourFront",
    "marina bay sands": "Bayfront",
    "mbs": "Bayfront",
    "orchard road": "Orchard",
    "clarke quay": "Clarke Quay",
    "dhoby ghaut": "Dhoby Ghaut",
    "city hall": "City Hall",
    "bugis": "Bugis",
    "jurong east": "Jurong East",
    "bishan": "Bishan",
    "woodlands": "Woodlands",
    "clementi": "Clementi",
}


def extract_station_name(location_query: str, default: str = "Tampines") -> str:
    """
    Intelligently maps arbitrary location inputs, postal codes, or landmark names
    to the nearest or matching Singapore MRT station name.
    """
    if not location_query:
        return default

    clean = location_query.strip().lower()

    # 1. Direct alias check
    for alias, station in STATION_ALIASES.items():
        if alias in clean:
            return station

    # 2. Extract station if user typed 'X MRT' or 'X Station'
    mrt_match = re.search(r'([A-Za-z\s]+)(?:mrt|station)', clean, re.IGNORECASE)
    if mrt_match:
        cand = mrt_match.group(1).strip().title()
        if len(cand) >= 3:
            return cand

    # 3. Clean string into Title Case candidate
    words = [w.capitalize() for w in clean.replace(",", " ").split() if len(w) > 2]
    if words:
        # Check consecutive pairs for names like "Jurong East"
        for i in range(len(words) - 1):
            pair = f"{words[i]} {words[i+1]}"
            if pair.lower() in STATION_ALIASES:
                return STATION_ALIASES[pair.lower()]
        return words[0]

    return default


def register_custom_persona(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Creates and registers an on-the-spot customized commuter profile.
    Allows new users to define their own corridor, preferred modes, and constraints.
    """
    name = str(data.get("name") or "New Commuter").strip()
    clean_id = re.sub(r'[^a-zA-Z0-9_]', '', name.lower().replace(" ", "_"))
    if not clean_id or clean_id in ("rachel", "arjun", "mdm_lim"):
        clean_id = f"custom_{len(ALL_PERSONAS) + 1}"

    origin = str(data.get("origin") or "Jurong East").strip()
    destination = str(data.get("destination") or "Bishan").strip()
    boarding_stn = extract_station_name(origin, default="Jurong East")
    alighting_stn = extract_station_name(destination, default="Bishan")

    departure_time = str(data.get("departure_time") or "08:00 AM").strip()
    deadline_arrival = str(data.get("deadline_arrival") or "08:50 AM").strip()
    delay_threshold = int(data.get("delay_threshold_min") or 15)

    cycling = bool(data.get("cycling_enabled", False))
    stair_aversion = bool(data.get("stair_aversion", False))
    walking_speed = float(data.get("walking_speed_mps") or (0.85 if stair_aversion else 1.35))

    profile = CommuterProfile(
        id=clean_id,
        name=name,
        persona=str(data.get("persona") or "On-The-Spot Custom Commuter"),
        tag=f"{boarding_stn} $\to$ {alighting_stn}",
        origin=origin,
        destination=destination,
        departure_time=departure_time,
        deadline_arrival=deadline_arrival,
        delay_threshold_min=delay_threshold,
        cycling_enabled=cycling,
        stair_aversion=stair_aversion,
        walking_speed_mps=walking_speed,
        boarding_station=boarding_stn,
        alighting_station=alighting_stn,
        is_custom=True,
    )

    profile_dict = profile.to_dict()
    ALL_PERSONAS[clean_id] = profile_dict
    return profile_dict


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
            "is_custom": p.get("is_custom", False),
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
