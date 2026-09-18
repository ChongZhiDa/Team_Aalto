"""
Commuter Persona profiles, behavioral constraints, and dynamic custom router.
Defines canonical personas (Rachel, Arjun, Mdm Lim) and provides
on-the-spot creation of customized commuter profiles and routes for arbitrary users.
"""

from dataclasses import dataclass, field, asdict
from typing import Dict, Any, List, Optional
import re
import json
import math
import os
import tempfile
from copy import deepcopy
from datetime import datetime, timedelta
from pathlib import Path
from uuid import uuid4


# ---------------------------------------------------------------------------
# CommuterProfile Dataclass
# ---------------------------------------------------------------------------

@dataclass
class CommuterProfile:
    """
    Typed, immutable-friendly representation of a commuter persona.
    Can be serialized to/from dict for JSON API transport.
    """
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
    cycling_speed_mps: float = 4.0
    primary_line: str = "MRT"
    boarding_station: str = "Jurong East"
    alighting_station: str = "Bishan"
    requires_step_free: bool = False
    requires_lift_monitoring: bool = False
    rain_shelter_priority: float = 0.8
    crowd_tolerance: str = "normal"     # "low", "normal", "high"
    is_custom: bool = True
    allowed_modes: List[str] = field(default_factory=lambda: ["WALK", "TRAIN", "CYCLE"])
    max_walking_distance_m: Optional[float] = None
    max_transfers: Optional[int] = None
    arrival_buffer_min: int = 15
    proactive_lead_min: int = 20
    crowd_advance_lead_min: int = 10
    avoid_cycling_in_rain: bool = True
    advice_tone: str = "calm, clear, decisive"
    advice_max_chars: int = 140
    transfer_station: Optional[str] = None
    alternative_route_name: Optional[str] = None
    alternative_recommendation: str = "ALTERNATIVE_ROUTE"

    def __post_init__(self) -> None:
        for key in ("id", "name", "persona", "origin", "destination",
                    "boarding_station", "alighting_station", "advice_tone",
                    "primary_line", "alternative_recommendation"):
            value = getattr(self, key)
            if not isinstance(value, str) or not value.strip():
                raise ValueError(f"{key} must be a non-empty string")
            setattr(self, key, value.strip())
        if not re.fullmatch(r"[a-z0-9_]+", self.id):
            raise ValueError("id must contain only lowercase letters, digits or underscores")
        for key in ("alternative_route_name", "transfer_station"):
            value = getattr(self, key)
            if value is not None and (not isinstance(value, str) or not value.strip()):
                raise ValueError(f"{key} must be a non-empty string or null")
        for key in ("stair_aversion", "cycling_enabled", "requires_step_free",
                    "requires_lift_monitoring", "is_custom", "avoid_cycling_in_rain"):
            setattr(self, key, parse_boolean(getattr(self, key), key))
        for key in ("normal_duration_min", "delay_threshold_min", "arrival_buffer_min",
                    "proactive_lead_min", "crowd_advance_lead_min", "advice_max_chars",
                    "max_transfers"):
            value = getattr(self, key)
            if value is None and key == "max_transfers":
                continue
            if isinstance(value, bool):
                raise ValueError(f"{key} must be a non-negative integer")
            try:
                number = float(value)
            except (TypeError, ValueError) as exc:
                raise ValueError(f"{key} must be a non-negative integer") from exc
            if not math.isfinite(number) or number < 0 or not number.is_integer():
                raise ValueError(f"{key} must be a non-negative integer")
            if key == "advice_max_chars" and number < 40:
                raise ValueError("advice_max_chars must be at least 40")
            setattr(self, key, int(number))
        for key in ("walking_speed_mps", "cycling_speed_mps", "rain_shelter_priority",
                    "max_walking_distance_m"):
            value = getattr(self, key)
            if value is None and key == "max_walking_distance_m":
                continue
            try:
                number = float(value)
            except (TypeError, ValueError) as exc:
                raise ValueError(f"{key} must be a finite number") from exc
            if isinstance(value, bool) or not math.isfinite(number) or number < 0:
                raise ValueError(f"{key} must be a finite non-negative number")
            if key.endswith("speed_mps") and number == 0:
                raise ValueError(f"{key} must be positive")
            if key == "rain_shelter_priority" and number > 1:
                raise ValueError("rain_shelter_priority must be between 0 and 1")
            setattr(self, key, number)
        for key in ("departure_time", "proactive_check_time", "deadline_arrival", "meeting_time"):
            parse_profile_time(getattr(self, key))
        if self.crowd_tolerance not in ("low", "normal", "high"):
            raise ValueError("crowd_tolerance must be low, normal or high")
        if not isinstance(self.allowed_modes, (list, tuple)) or not self.allowed_modes:
            raise ValueError("allowed_modes must be a non-empty list")
        self.allowed_modes = list(dict.fromkeys(str(mode).upper() for mode in self.allowed_modes))
        if set(self.allowed_modes) - {"WALK", "TRAIN", "CYCLE", "BUS"}:
            raise ValueError("allowed_modes supports WALK, TRAIN, CYCLE and BUS")

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'CommuterProfile':
        unknown = set(data) - set(cls.__dataclass_fields__)
        if unknown:
            raise ValueError(f"Unknown profile fields: {', '.join(sorted(unknown))}")
        return cls(**deepcopy(data))

    def derive_walk_duration_min(self, distance_m: float) -> float:
        """Calculates walking duration in minutes from distance and personal walking speed."""
        if self.walking_speed_mps <= 0:
            return distance_m / 1.35 / 60.0
        return distance_m / self.walking_speed_mps / 60.0

    def derive_cycle_duration_min(self, distance_m: float) -> float:
        """Calculates cycling duration in minutes from distance and personal cycling speed."""
        speed = self.cycling_speed_mps if self.cycling_speed_mps > 0 else 4.0
        return distance_m / speed / 60.0


def parse_boolean(value: Any, field_name: str) -> bool:
    """Accept JSON booleans and explicit boolean strings, never bool('false')."""
    if isinstance(value, bool):
        return value
    if isinstance(value, str) and value.strip().lower() in ("true", "false"):
        return value.strip().lower() == "true"
    raise ValueError(f"{field_name} must be true or false")


def parse_profile_time(value: str) -> datetime:
    if isinstance(value, str):
        for fmt in ("%I:%M %p", "%H:%M"):
            try:
                return datetime.strptime(value.strip().upper(), fmt)
            except ValueError:
                pass
    raise ValueError(f"Invalid time {value!r}; use HH:MM or HH:MM AM/PM")


# ---------------------------------------------------------------------------
# Canonical Persona Profiles
# ---------------------------------------------------------------------------

def _load_presets() -> Dict[str, Dict[str, Any]]:
    """Load editable preset defaults while keeping the legacy exported names."""
    path = Path(__file__).with_name("persona_presets.json")
    payload = json.loads(path.read_text(encoding="utf-8"))
    if payload.get("version") != 1 or not isinstance(payload.get("profiles"), list):
        raise ValueError("persona_presets.json must contain version 1 and a profiles list")
    profiles = [CommuterProfile.from_dict(data).to_dict() for data in payload["profiles"]]
    presets = {profile["id"]: profile for profile in profiles}
    if len(presets) != len(profiles):
        raise ValueError("Duplicate IDs in persona_presets.json")
    if not {"rachel", "arjun", "mdm_lim"}.issubset(presets):
        raise ValueError("The legacy rachel, arjun and mdm_lim preset IDs are required")
    if any(profile["is_custom"] for profile in profiles):
        raise ValueError("Preset profiles must have is_custom=false")
    return presets


_PRESET_PROFILES = _load_presets()
RACHEL_PROFILE: Dict[str, Any] = _PRESET_PROFILES["rachel"]
ARJUN_PROFILE: Dict[str, Any] = _PRESET_PROFILES["arjun"]
MDM_LIM_PROFILE: Dict[str, Any] = _PRESET_PROFILES["mdm_lim"]


# ---------------------------------------------------------------------------
# Persona Registry
# ---------------------------------------------------------------------------

ALL_PERSONAS: Dict[str, Dict[str, Any]] = dict(_PRESET_PROFILES)

_CURRENT_ACTIVE_PERSONA_ID: str = "rachel"


# ---------------------------------------------------------------------------
# Station Alias Map (Landmark / Street → MRT Station Name)
# ---------------------------------------------------------------------------

STATION_ALIASES: Dict[str, str] = {
    # Common landmarks & abbreviations
    "cbd": "Raffles Place",
    "one raffles place": "Raffles Place",
    "raffles": "Raffles Place",
    "sgh": "Outram Park",
    "singapore general hospital": "Outram Park",
    "fusionopolis": "one-north",
    "biopolis": "one-north",
    "one north": "one-north",
    "one-north": "one-north",
    "nus": "Kent Ridge",
    "national university": "Kent Ridge",
    "ntu": "Pioneer",
    "nanyang technological": "Pioneer",
    "changi": "Changi Airport",
    "airport": "Changi Airport",
    "sentosa": "HarbourFront",
    "vivo city": "HarbourFront",
    "vivocity": "HarbourFront",
    "marina bay sands": "Bayfront",
    "mbs": "Bayfront",
    "gardens by the bay": "Bayfront",
    "orchard road": "Orchard",
    "ion orchard": "Orchard",
    "takashimaya": "Orchard",

    # Street address → nearest station
    "tampines st": "Tampines",
    "tampines ave": "Tampines",
    "tampines street": "Tampines",
    "punggol field": "Punggol",
    "punggol walk": "Punggol",
    "bedok north": "Bedok North",
    "bedok reservoir": "Bedok Reservoir",
    "jurong east st": "Jurong East",
    "clementi ave": "Clementi",
    "woodlands ave": "Woodlands",
    "woodlands drive": "Woodlands",
    "ang mo kio ave": "Ang Mo Kio",
    "toa payoh": "Toa Payoh",
    "bukit merah": "Redhill",
    "queenstown": "Queenstown",
    "yishun": "Yishun",
    "sengkang": "Sengkang",
    "hougang": "Hougang",
    "serangoon": "Serangoon",

    # Station name aliases (lowercase for matching)
    "harbourfront": "HarbourFront",
    "clarke quay": "Clarke Quay",
    "dhoby ghaut": "Dhoby Ghaut",
    "city hall": "City Hall",
    "bugis": "Bugis",
    "jurong east": "Jurong East",
    "bishan": "Bishan",
    "woodlands": "Woodlands",
    "clementi": "Clementi",
    "pasir ris": "Pasir Ris",
    "tampines": "Tampines",
    "simei": "Simei",
    "tanah merah": "Tanah Merah",
    "expo": "Expo",
    "paya lebar": "Paya Lebar",
    "kallang": "Kallang",
    "lavender": "Lavender",
    "raffles place": "Raffles Place",
    "tanjong pagar": "Tanjong Pagar",
    "outram park": "Outram Park",
    "tiong bahru": "Tiong Bahru",
    "redhill": "Redhill",
    "buona vista": "Buona Vista",
    "dover": "Dover",
    "ang mo kio": "Ang Mo Kio",
    "marina bay": "Marina Bay",
    "bayfront": "Bayfront",
    "promenade": "Promenade",
    "esplanade": "Esplanade",
    "bras basah": "Bras Basah",
    "chinatown": "Chinatown",
    "little india": "Little India",
    "farrer park": "Farrer Park",
    "newton": "Newton",
    "orchard": "Orchard",
    "somerset": "Somerset",
    "botanic gardens": "Botanic Gardens",
    "kent ridge": "Kent Ridge",
    "pioneer": "Pioneer",
    "boon lay": "Boon Lay",
    "choa chu kang": "Choa Chu Kang",
    "bukit batok": "Bukit Batok",
    "punggol": "Punggol",
    "sengkang": "Sengkang",
    "hougang": "Hougang",
    "kovan": "Kovan",
    "potong pasir": "Potong Pasir",
    "macpherson": "MacPherson",
    "bedok": "Bedok",
}


def extract_station_name(location_query: str, default: str = "Tampines") -> str:
    """
    Intelligently maps arbitrary location inputs — street addresses, postal codes,
    landmark names, or informal station references — to the nearest Singapore MRT
    station name recognized by the graph router.

    Resolution order:
    1. Direct alias match (longest-match-first for specificity)
    2. "X MRT" / "X Station" pattern extraction
    3. Title-cased first significant word
    """
    if not location_query:
        return default

    clean = location_query.strip().lower()

    # 1. Sort aliases by length descending so "one raffles place" matches before "raffles"
    for alias in sorted(STATION_ALIASES.keys(), key=len, reverse=True):
        if alias in clean:
            return STATION_ALIASES[alias]

    # 2. Extract station if user typed 'X MRT' or 'X Station'
    mrt_match = re.search(r'([A-Za-z\s]+?)(?:\s+mrt|\s+station)', clean, re.IGNORECASE)
    if mrt_match:
        cand = mrt_match.group(1).strip().title()
        if len(cand) >= 3:
            return cand

    # 3. Clean string into Title Case candidate
    words = [w.capitalize() for w in clean.replace(",", " ").split() if len(w) > 2]
    if words:
        # Check consecutive pairs for compound names like "Jurong East"
        for i in range(len(words) - 1):
            pair = f"{words[i]} {words[i+1]}"
            if pair.lower() in STATION_ALIASES:
                return STATION_ALIASES[pair.lower()]
        return words[0]

    return default


# ---------------------------------------------------------------------------
# Persona CRUD Operations
# ---------------------------------------------------------------------------

def register_custom_persona(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Creates and registers an on-the-spot customized commuter profile.
    Allows new users to define their own corridor, preferred modes, and constraints.
    Returns the registered profile dict.
    """
    supplied = deepcopy(data)
    template_id = supplied.pop("template_id", None)
    values = get_persona(template_id, strict=True) if template_id else {}
    values.update(supplied)
    values["id"] = supplied.get("id", f"custom_{uuid4().hex}")
    if values["id"] in ALL_PERSONAS:
        raise ValueError("Profile ID already exists; use update_persona to edit it")
    values.setdefault("name", "New Commuter")
    values.setdefault("persona", "On-The-Spot Custom Commuter")
    values["is_custom"] = True
    _derive_profile_fields(values, supplied, new_profile=not bool(template_id))
    profile_dict = CommuterProfile.from_dict(values).to_dict()
    ALL_PERSONAS[profile_dict["id"]] = profile_dict
    return deepcopy(profile_dict)


def _derive_profile_fields(values: Dict[str, Any], supplied: Dict[str, Any],
                           new_profile: bool = False) -> None:
    """Derive related values only when the caller did not supply an override."""
    defaults = CommuterProfile(id="defaults", name="Defaults", persona="Defaults").to_dict()
    normalized = CommuterProfile.from_dict({**defaults, **values})
    for location, station in (("origin", "boarding_station"), ("destination", "alighting_station")):
        if station not in supplied and (location in supplied or new_profile):
            values[station] = extract_station_name(values.get(location, defaults[location]),
                                                   default=defaults[station])
    departure = parse_profile_time(normalized.departure_time)
    if "proactive_check_time" not in supplied and (new_profile or set(supplied) & {"departure_time", "proactive_lead_min"}):
        values["proactive_check_time"] = (departure - timedelta(minutes=normalized.proactive_lead_min)).strftime("%I:%M %p")
    if "deadline_arrival" not in supplied and (new_profile or set(supplied) & {"departure_time", "normal_duration_min", "arrival_buffer_min"}):
        values["deadline_arrival"] = (departure + timedelta(minutes=normalized.normal_duration_min + normalized.arrival_buffer_min)).strftime("%I:%M %p")
    if "tag" not in supplied and (new_profile or set(supplied) & {"origin", "destination", "boarding_station", "alighting_station"}):
        values["tag"] = (f"{values.get('boarding_station', defaults['boarding_station'])} to "
                         f"{values.get('alighting_station', defaults['alighting_station'])}")
    if set(supplied) & {"origin", "destination"}:
        # A configured bypass belongs to its original corridor.
        if "alternative_route_name" not in supplied:
            values["alternative_route_name"] = None


def update_persona(persona_id: str, changes: Dict[str, Any]) -> Dict[str, Any]:
    """Edit a profile or preset without changing its identity or custom status."""
    values = get_persona(persona_id, strict=True)
    if set(changes) & {"id", "is_custom", "template_id"}:
        raise ValueError("Cannot update id, is_custom or template_id")
    values.update(deepcopy(changes))
    _derive_profile_fields(values, changes)
    profile_dict = CommuterProfile.from_dict(values).to_dict()
    # Preserve references imported by existing callers, including the master files.
    ALL_PERSONAS[profile_dict["id"]].clear()
    ALL_PERSONAS[profile_dict["id"]].update(profile_dict)
    return deepcopy(profile_dict)


def save_personas(path: str) -> None:
    """Explicitly save all editable presets and custom profiles as JSON."""
    target = Path(path)
    payload = {"version": 1, "profiles": [CommuterProfile.from_dict(p).to_dict()
                                         for p in ALL_PERSONAS.values()]}
    target.parent.mkdir(parents=True, exist_ok=True)
    temporary = None
    try:
        with tempfile.NamedTemporaryFile(mode="w", encoding="utf-8", dir=target.parent,
                                         suffix=".tmp", delete=False) as stream:
            temporary = stream.name
            json.dump(payload, stream, indent=2, ensure_ascii=False)
            stream.write("\n")
        os.replace(temporary, target)
    finally:
        if temporary and os.path.exists(temporary):
            os.unlink(temporary)


def load_personas(path: str) -> List[Dict[str, Any]]:
    """Validate an entire configuration before applying any profile changes."""
    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(payload, dict) or payload.get("version") != 1 or not isinstance(payload.get("profiles"), list):
        raise ValueError("Expected version 1 and a profiles list")
    profiles = [CommuterProfile.from_dict(p).to_dict() for p in payload["profiles"]]
    if len({p["id"] for p in profiles}) != len(profiles):
        raise ValueError("Duplicate profile IDs in configuration")
    for profile in profiles:
        if profile["id"] in _PRESET_PROFILES and profile["is_custom"]:
            raise ValueError("Preset IDs cannot be used for custom profiles")
    for profile in profiles:
        if profile["id"] in ALL_PERSONAS:
            ALL_PERSONAS[profile["id"]].clear()
            ALL_PERSONAS[profile["id"]].update(profile)
        else:
            ALL_PERSONAS[profile["id"]] = profile
    return deepcopy(profiles)


def delete_custom_persona(persona_id: str) -> bool:
    """
    Removes a custom persona from the registry.
    Cannot delete canonical personas (rachel, arjun, mdm_lim).
    """
    global _CURRENT_ACTIVE_PERSONA_ID
    clean_id = str(persona_id).strip().lower()
    if clean_id in ALL_PERSONAS and not ALL_PERSONAS[clean_id].get("is_custom", False):
        return False
    if clean_id in ALL_PERSONAS:
        del ALL_PERSONAS[clean_id]
        if _CURRENT_ACTIVE_PERSONA_ID == clean_id:
            _CURRENT_ACTIVE_PERSONA_ID = "rachel"
        return True
    return False


def get_persona(persona_id: str, strict: bool = False) -> Dict[str, Any]:
    """Retrieves persona profile dictionary by ID, defaulting to Rachel."""
    clean_id = str(persona_id).strip().lower()
    if strict and clean_id not in ALL_PERSONAS:
        raise ValueError(f"Unknown persona: {persona_id}")
    return deepcopy(ALL_PERSONAS.get(clean_id, RACHEL_PROFILE))


def list_personas() -> List[Dict[str, Any]]:
    """Returns list of all available persona profiles for selection."""
    return [
        CommuterProfile.from_dict(p).to_dict()
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
    return get_persona(_CURRENT_ACTIVE_PERSONA_ID)


def get_custom_personas() -> List[Dict[str, Any]]:
    """Returns only user-created custom personas (excludes canonical Rachel/Arjun/Mdm Lim)."""
    return [deepcopy(p) for p in ALL_PERSONAS.values() if p.get("is_custom", False)]
