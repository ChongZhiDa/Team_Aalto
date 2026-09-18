"""
GeoJSON loader and polygon processor for LTA Rail Station boundaries.
Parses data/AmendmenttoMP2014RailStation.geojson to extract:
- Official polygon geometry
- Centroid coordinates [lat, lon]
- Ground level (UNDERGROUND vs ABOVEGROUND)
- Station transport type (MRT, LRT, CCL)
"""

import os
import json
import re
from typing import Dict, Any, Optional, List, Tuple

# Cache for loaded stations to prevent re-reading on every request
_GEOJSON_STATIONS_CACHE: Optional[Dict[str, Dict[str, Any]]] = None


def normalize_station_name(raw_name: Optional[str]) -> str:
    """
    Cleans raw GeoJSON station names like 'BUGIS MRT STATION' -> 'BUGIS',
    'BISHAN INTERCHANGE' -> 'BISHAN', 'ONE NORTH' -> 'ONE-NORTH'.
    """
    if not raw_name:
        return ""
    name = raw_name.upper().strip()
    name = re.sub(r"\s+(MRT|LRT)?\s*(STATION|INTERCHANGE)$", "", name)
    name = re.sub(r"\s+(MRT|LRT)$", "", name)
    name = name.strip()
    if name == "ONE NORTH":
        name = "ONE-NORTH"
    return name


def compute_polygon_centroid(coordinates: List[List[float]]) -> Tuple[float, float]:
    """
    Computes polygon centroid [lat, lon] from GeoJSON [[lon, lat], ...].
    """
    if not coordinates:
        return (1.3521, 103.8198)  # Default Singapore center
    lats = [pt[1] for pt in coordinates]
    lons = [pt[0] for pt in coordinates]
    centroid_lat = sum(lats) / len(lats)
    centroid_lon = sum(lons) / len(lons)
    return (round(centroid_lat, 5), round(centroid_lon, 5))


def find_geojson_path() -> Optional[str]:
    """Locates AmendmenttoMP2014RailStation.geojson in relative or absolute paths."""
    potential_paths = [
        os.path.join(os.path.dirname(__file__), "..", "..", "data", "AmendmenttoMP2014RailStation.geojson"),
        os.path.join("data", "AmendmenttoMP2014RailStation.geojson"),
        os.path.join("PS2", "data", "AmendmenttoMP2014RailStation.geojson"),
        os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "data", "AmendmenttoMP2014RailStation.geojson")),
    ]
    for path in potential_paths:
        if os.path.exists(path):
            return path
    return None


def load_geojson_stations(force_reload: bool = False) -> Dict[str, Dict[str, Any]]:
    """
    Loads and indexes all 208 station polygons from the official GeoJSON.
    Returns a dictionary keyed by normalized station name:
    {
        "BUGIS": {
            "name": "BUGIS",
            "coords": [1.30043, 103.85569], # [lat, lon]
            "grnd_level": "UNDERGROUND",
            "type": "MRT",
            "polygon": [[[lon, lat], ...]],
            "area": 8935.2,
            "object_id": 661
        }
    }
    """
    global _GEOJSON_STATIONS_CACHE
    if _GEOJSON_STATIONS_CACHE is not None and not force_reload:
        return _GEOJSON_STATIONS_CACHE

    geojson_path = find_geojson_path()
    stations_map: Dict[str, Dict[str, Any]] = {}

    if not geojson_path or not os.path.exists(geojson_path):
        _GEOJSON_STATIONS_CACHE = stations_map
        return stations_map

    try:
        with open(geojson_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        for feature in data.get("features", []):
            props = feature.get("properties", {})
            raw_name = props.get("NAME")
            if not raw_name:
                continue

            clean_name = normalize_station_name(raw_name)
            geometry = feature.get("geometry", {})
            geom_type = geometry.get("type")
            coords_raw = geometry.get("coordinates", [])

            if geom_type == "Polygon" and coords_raw:
                outer_ring = coords_raw[0]
                centroid_lat, centroid_lon = compute_polygon_centroid(outer_ring)
            elif geom_type == "MultiPolygon" and coords_raw:
                outer_ring = coords_raw[0][0]
                centroid_lat, centroid_lon = compute_polygon_centroid(outer_ring)
            else:
                continue

            grnd_level = props.get("GRND_LEVEL", "UNKNOWN")
            station_type = props.get("TYPE", "MRT")
            area = props.get("SHAPE_1.AREA", 0.0)
            object_id = props.get("OBJECTID", 0)

            # Store or merge (if interchange has multiple line polygon records, prefer underground)
            if clean_name not in stations_map or grnd_level == "UNDERGROUND":
                stations_map[clean_name] = {
                    "name": clean_name,
                    "coords": [centroid_lat, centroid_lon],
                    "grnd_level": grnd_level,
                    "type": station_type,
                    "polygon": outer_ring,
                    "area": area,
                    "object_id": object_id,
                }

    except Exception as e:
        print(f"Warning: Failed to parse Rail Station GeoJSON: {e}")

    _GEOJSON_STATIONS_CACHE = stations_map
    return stations_map


def get_station_metadata(station_name: str) -> Optional[Dict[str, Any]]:
    """Returns official GeoJSON metadata (centroid, ground level, type) for a station."""
    stations = load_geojson_stations()
    normalized = normalize_station_name(station_name)
    return stations.get(normalized)


def find_nearest_station(lat: float, lon: float) -> Tuple[Optional[Dict[str, Any]], float]:
    """
    Finds the nearest MRT/LRT station to given coordinates.
    Returns (station_dict, distance_in_meters).
    """
    stations = load_geojson_stations()
    if not stations:
        return (None, float("inf"))

    nearest_stn = None
    min_dist_m = float("inf")

    for stn in stations.values():
        stn_lat, stn_lon = stn["coords"]
        dy = (lat - stn_lat) * 111000.0
        dx = (lon - stn_lon) * 110970.0
        dist_m = (dx * dx + dy * dy) ** 0.5
        if dist_m < min_dist_m:
            min_dist_m = dist_m
            nearest_stn = stn

    return (nearest_stn, round(min_dist_m, 1))


def get_station_polygon(station_name: str) -> Optional[List[List[float]]]:
    """Returns outer polygon boundary coordinates [[lon, lat], ...] for station footprint rendering."""
    meta = get_station_metadata(station_name)
    if meta:
        return meta.get("polygon")
    return None

