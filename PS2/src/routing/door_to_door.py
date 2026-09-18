"""
Door-to-door pedestrian first/last-mile walking calculations.
Incorporates sheltered linkways (CoveredLinkWay) and walking speed assumptions.
"""

from typing import Dict, Any
from .coordinates import ORIGIN_POINT, DESTINATION_POINT, EWL_STATIONS, DTL_STATIONS


def get_walking_legs() -> Dict[str, Any]:
    """
    Returns pedestrian connections for first/last mile legs:
    - Distance in meters
    - Walk duration in minutes (based on 1.35 m/s walking speed)
    - Sheltered percentage (from LTA CoveredLinkWay data)
    - Coordinates polyline
    """
    return {
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
    }

