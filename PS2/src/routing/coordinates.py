"""
Geospatial coordinates, MRT station nodes, and transit corridors.
Teammate B can add new lines, stations, or import GeoJSON centroids here.
"""

from typing import List, Dict, Any

ORIGIN_POINT = {
    "name": "Rachel's Home (Blk 230 Tampines St 21)",
    "coords": [1.3556, 103.9495],
}

DESTINATION_POINT = {
    "name": "Rachel's Office (One Raffles Place)",
    "coords": [1.2840, 103.8515],
}

# East-West Line Stations (Tampines to Raffles Place)
EWL_STATIONS: List[Dict[str, Any]] = [
    {"code": "EW2", "name": "Tampines", "coords": [1.3533, 103.9452]},
    {"code": "EW3", "name": "Simei", "coords": [1.3432, 103.9533]},
    {"code": "EW4", "name": "Tanah Merah", "coords": [1.3273, 103.9463]},
    {"code": "EW5", "name": "Bedok", "coords": [1.3240, 103.9300]},
    {"code": "EW6", "name": "Kembangan", "coords": [1.3210, 103.9129]},
    {"code": "EW7", "name": "Eunos", "coords": [1.3197, 103.9030]},
    {"code": "EW8", "name": "Paya Lebar", "coords": [1.3178, 103.8924]},
    {"code": "EW9", "name": "Aljunied", "coords": [1.3164, 103.8829]},
    {"code": "EW10", "name": "Kallang", "coords": [1.3115, 103.8714]},
    {"code": "EW11", "name": "Lavender", "coords": [1.3073, 103.8628]},
    {"code": "EW12", "name": "Bugis", "coords": [1.3005, 103.8559]},
    {"code": "EW13", "name": "City Hall", "coords": [1.2930, 103.8521]},
    {"code": "EW14", "name": "Raffles Place", "coords": [1.2840, 103.8515]},
]

# Downtown Line Stations (Tampines Downtown to Telok Ayer)
DTL_STATIONS: List[Dict[str, Any]] = [
    {"code": "DT32", "name": "Tampines", "coords": [1.3528, 103.9439]},
    {"code": "DT31", "name": "Tampines West", "coords": [1.3456, 103.9384]},
    {"code": "DT30", "name": "Bedok Reservoir", "coords": [1.3364, 103.9329]},
    {"code": "DT29", "name": "Bedok North", "coords": [1.3347, 103.9179]},
    {"code": "DT28", "name": "Kaki Bukit", "coords": [1.3349, 103.9084]},
    {"code": "DT27", "name": "Ubi", "coords": [1.3299, 103.8993]},
    {"code": "DT26", "name": "MacPherson", "coords": [1.3259, 103.8899]},
    {"code": "DT25", "name": "Mattar", "coords": [1.3268, 103.8832]},
    {"code": "DT24", "name": "Geylang Bahru", "coords": [1.3214, 103.8716]},
    {"code": "DT23", "name": "Bendemeer", "coords": [1.3138, 103.8629]},
    {"code": "DT22", "name": "Jalan Besar", "coords": [1.3053, 103.8553]},
    {"code": "DT21", "name": "Bencoolen", "coords": [1.2988, 103.8507]},
    {"code": "DT20", "name": "Fort Canning", "coords": [1.2925, 103.8443]},
    {"code": "DT19", "name": "Chinatown", "coords": [1.2848, 103.8440]},
    {"code": "DT18", "name": "Telok Ayer", "coords": [1.2822, 103.8486]},
]

# Express Bus 10e Path Waypoints
BUS_10E_WAYPOINTS: List[Dict[str, Any]] = [
    {"name": "Blk 230 Tampines St 21", "coords": [1.3556, 103.9495]},
    {"name": "Bus Stop 76239 (Tampines Ave 7)", "coords": [1.3562, 103.9470]},
    {"name": "ECP Expressway Corridor", "coords": [1.3045, 103.9015]},
    {"name": "Marina Boulevard", "coords": [1.2798, 103.8540]},
    {"name": "Bus Stop 03019 (Fullerton Sq)", "coords": [1.2858, 103.8528]},
    {"name": "One Raffles Place", "coords": [1.2840, 103.8515]},
]


def get_ewl_polyline() -> List[List[float]]:
    return [s["coords"] for s in EWL_STATIONS]


def get_dtl_polyline() -> List[List[float]]:
    return [s["coords"] for s in DTL_STATIONS]


def get_bus10e_polyline() -> List[List[float]]:
    return [w["coords"] for w in BUS_10E_WAYPOINTS]

