"""
Door-to-door pedestrian first/last-mile walking calculations.
Incorporates sheltered linkways (LTA CoveredLinkWay data), walking speed assumptions,
and dynamic rain delay penalties.
"""

from typing import Dict, Any, Optional
from .coordinates import ORIGIN_POINT, DESTINATION_POINT, EWL_STATIONS, DTL_STATIONS


# Baseline Walking Leg Geometries & Attributes
BASE_WALKING_LEGS: Dict[str, Any] = {
    "home_to_tampines_ewl": {
        "name": "Walk: Home to Tampines MRT (EW2)",
        "duration_min": 6,
        "distance_m": 520,
        "sheltered_percent": 80,
        "coords": [ORIGIN_POINT["coords"], [1.3540, 103.9475], EWL_STATIONS[0]["coords"]],
    },
    "home_to_tampines_dtl": {
        "name": "Walk: Home to Tampines Downtown MRT (DT32)",
        "duration_min": 5,
        "distance_m": 450,
        "sheltered_percent": 90,
        "coords": [ORIGIN_POINT["coords"], [1.3538, 103.9460], DTL_STATIONS[0]["coords"]],
    },
    "raffles_place_ewl_to_desk": {
        "name": "Walk: Raffles Place MRT Exit B to Office Desk",
        "duration_min": 2,
        "distance_m": 120,
        "sheltered_percent": 100,
        "coords": [EWL_STATIONS[-1]["coords"], DESTINATION_POINT["coords"]],
    },
    "telok_ayer_dtl_to_desk": {
        "name": "Walk: Telok Ayer MRT Exit B via Cross St to Office Desk",
        "duration_min": 5,
        "distance_m": 410,
        "sheltered_percent": 95,
        "coords": [DTL_STATIONS[-1]["coords"], [1.2833, 103.8500], DESTINATION_POINT["coords"]],
    },
    "home_to_bus10e": {
        "name": "Walk: Home to Tampines Ave 7 Bus Stop",
        "duration_min": 4,
        "distance_m": 320,
        "sheltered_percent": 50,  # Open roadside footpath
        "coords": [ORIGIN_POINT["coords"], [1.3562, 103.9470]],
    },
    "fullerton_bus10e_to_desk": {
        "name": "Walk: Fullerton Sq to One Raffles Place",
        "duration_min": 3,
        "distance_m": 220,
        "sheltered_percent": 60,
        "coords": [[1.2858, 103.8528], DESTINATION_POINT["coords"]],
    },
}


def calculate_rain_penalty(duration_min: int, sheltered_percent: int, rain_active: bool) -> float:
    """
    Calculates dynamic rain penalty in minutes.
    Unsheltered footpaths incur walking slowdown (avoiding puddles, holding umbrellas,
    or detouring to adjacent covered linkways).
    100% sheltered = 0 min penalty.
    50% sheltered = +2 to +3 min penalty.
    """
    if not rain_active or sheltered_percent >= 100:
        return 0.0
    unsheltered_pct = (100 - sheltered_percent) / 100.0
    # Penalty model: 60% slower speed on unsheltered segments + 1 min detour buffer
    penalty = (duration_min * unsheltered_pct * 0.6) + (1.0 if unsheltered_pct > 0.25 else 0.5)
    return round(penalty, 1)


def get_walking_legs(rain_active: bool = False) -> Dict[str, Any]:
    """
    Returns pedestrian connections for first/last mile legs.
    If rain_active=True, adjusts durations and sheltered scores dynamically.
    """
    legs: Dict[str, Any] = {}
    for key, leg in BASE_WALKING_LEGS.items():
        base_dur = leg["duration_min"]
        shelter = leg["sheltered_percent"]
        rain_delay = calculate_rain_penalty(base_dur, shelter, rain_active)
        effective_dur = int(round(base_dur + rain_delay))

        legs[key] = {
            **leg,
            "duration_min": effective_dur,
            "base_duration_min": base_dur,
            "rain_delay_min": rain_delay,
            "is_rain_penalized": rain_delay > 0,
            "shelter_status": "Fully Covered" if shelter == 100 else f"{shelter}% Sheltered",
        }
    return legs


def compute_walking_summary(rain_active: bool = False, corridor: str = "ewl") -> Dict[str, Any]:
    """
    Computes aggregated first-and-last mile walking summary.
    Allows comparing dry vs rain penalties for route optimization.
    """
    legs = get_walking_legs(rain_active=rain_active)
    if corridor == "dtl":
        walk_keys = ["home_to_tampines_dtl", "telok_ayer_dtl_to_desk"]
    elif corridor == "bus":
        walk_keys = ["home_to_bus10e", "fullerton_bus10e_to_desk"]
    else:
        walk_keys = ["home_to_tampines_ewl", "raffles_place_ewl_to_desk"]

    total_dist = sum(legs[k]["distance_m"] for k in walk_keys)
    total_dur = sum(legs[k]["duration_min"] for k in walk_keys)
    base_dur = sum(legs[k]["base_duration_min"] for k in walk_keys)
    avg_shelter = round(sum(legs[k]["sheltered_percent"] for k in walk_keys) / len(walk_keys), 1)

    return {
        "corridor": corridor,
        "rain_active": rain_active,
        "total_walk_min": total_dur,
        "base_walk_min": base_dur,
        "rain_delay_min": round(total_dur - base_dur, 1),
        "total_distance_m": total_dist,
        "avg_sheltered_percent": avg_shelter,
        "legs": [legs[k] for k in walk_keys],
    }
