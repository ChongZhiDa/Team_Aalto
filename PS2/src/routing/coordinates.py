"""
Geospatial coordinates, MRT station nodes, and transit corridors.
Integrates official station boundary polygons from AmendmenttoMP2014RailStation.geojson:
- Extracts exact polygon centroids
- Enriches stations with GRND_LEVEL (UNDERGROUND vs ABOVEGROUND)
- Provides full island station index and line polylines
"""

from typing import List, Dict, Any, Optional
from .geojson_loader import load_geojson_stations, get_station_metadata

ORIGIN_POINT = {
    "name": "Rachel's Home (Blk 230 Tampines St 21)",
    "coords": [1.3556, 103.9495],
}

DESTINATION_POINT = {
    "name": "Rachel's Office (One Raffles Place)",
    "coords": [1.2840, 103.8515],
}

# Base Station Lists with Codes
_RAW_EWL_STATIONS = [
    {"code": "EW2", "name": "Tampines", "default_coords": [1.3533, 103.9452]},
    {"code": "EW3", "name": "Simei", "default_coords": [1.3432, 103.9533]},
    {"code": "EW4", "name": "Tanah Merah", "default_coords": [1.3273, 103.9463]},
    {"code": "EW5", "name": "Bedok", "default_coords": [1.3240, 103.9300]},
    {"code": "EW6", "name": "Kembangan", "default_coords": [1.3210, 103.9129]},
    {"code": "EW7", "name": "Eunos", "default_coords": [1.3197, 103.9030]},
    {"code": "EW8", "name": "Paya Lebar", "default_coords": [1.3178, 103.8924]},
    {"code": "EW9", "name": "Aljunied", "default_coords": [1.3164, 103.8829]},
    {"code": "EW10", "name": "Kallang", "default_coords": [1.3115, 103.8714]},
    {"code": "EW11", "name": "Lavender", "default_coords": [1.3073, 103.8628]},
    {"code": "EW12", "name": "Bugis", "default_coords": [1.3005, 103.8559]},
    {"code": "EW13", "name": "City Hall", "default_coords": [1.2930, 103.8521]},
    {"code": "EW14", "name": "Raffles Place", "default_coords": [1.2840, 103.8515]},
]

_RAW_DTL_STATIONS = [
    {"code": "DT32", "name": "Tampines", "default_coords": [1.3528, 103.9439]},
    {"code": "DT31", "name": "Tampines West", "default_coords": [1.3456, 103.9384]},
    {"code": "DT30", "name": "Bedok Reservoir", "default_coords": [1.3364, 103.9329]},
    {"code": "DT29", "name": "Bedok North", "default_coords": [1.3347, 103.9179]},
    {"code": "DT28", "name": "Kaki Bukit", "default_coords": [1.3349, 103.9084]},
    {"code": "DT27", "name": "Ubi", "default_coords": [1.3299, 103.8993]},
    {"code": "DT26", "name": "MacPherson", "default_coords": [1.3259, 103.8899]},
    {"code": "DT25", "name": "Mattar", "default_coords": [1.3268, 103.8832]},
    {"code": "DT24", "name": "Geylang Bahru", "default_coords": [1.3214, 103.8716]},
    {"code": "DT23", "name": "Bendemeer", "default_coords": [1.3138, 103.8629]},
    {"code": "DT22", "name": "Jalan Besar", "default_coords": [1.3053, 103.8553]},
    {"code": "DT21", "name": "Bencoolen", "default_coords": [1.2988, 103.8507]},
    {"code": "DT20", "name": "Fort Canning", "default_coords": [1.2925, 103.8443]},
    {"code": "DT19", "name": "Chinatown", "default_coords": [1.2848, 103.8440]},
    {"code": "DT18", "name": "Telok Ayer", "default_coords": [1.2822, 103.8486]},
]


def _enrich_station(stn: Dict[str, Any]) -> Dict[str, Any]:
    """Enriches a station dictionary with official GeoJSON centroid and attributes."""
    meta = get_station_metadata(stn["name"])
    if meta:
        coords = meta["coords"]
        grnd_level = meta["grnd_level"]
        area = meta.get("area", 0.0)
    else:
        coords = stn.get("default_coords", [1.3521, 103.8198])
        grnd_level = "UNDERGROUND" if "Raffles" in stn["name"] or "City" in stn["name"] or "Bugis" in stn["name"] else "ABOVEGROUND"
        area = 0.0

    return {
        "code": stn["code"],
        "name": stn["name"],
        "coords": coords,
        "grnd_level": grnd_level,
        "is_underground": grnd_level == "UNDERGROUND",
        "polygon_area": area,
    }


# Enriched station sequences using official GeoJSON
EWL_STATIONS: List[Dict[str, Any]] = [_enrich_station(s) for s in _RAW_EWL_STATIONS]
DTL_STATIONS: List[Dict[str, Any]] = [_enrich_station(s) for s in _RAW_DTL_STATIONS]

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


def get_station_by_name(name: str) -> Optional[Dict[str, Any]]:
    """Returns station details (coords, grnd_level) from GeoJSON or corridor list."""
    meta = get_station_metadata(name)
    if meta:
        return meta
    for s in EWL_STATIONS + DTL_STATIONS:
        if s["name"].lower() == name.lower():
            return s
    return None
