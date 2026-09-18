"""
Routing and Geospatial package:
- coordinates: Station waypoints, line tracks, origin/destinations, and GeoJSON enrichment
- door_to_door: Pedestrian walking legs, sheltered linkway connectivity, and dynamic rain penalties
- multimodal_router: Journey duration, delay impact, platform transfers, and arbitrary graph routing
- geojson_loader: Official LTA Rail Station boundary polygon parser
- graph_router: Singapore MRT network graph pathfinder with transfer penalties
"""

from .coordinates import (
    ORIGIN_POINT,
    DESTINATION_POINT,
    EWL_STATIONS,
    DTL_STATIONS,
    BUS_10E_WAYPOINTS,
    get_ewl_polyline,
    get_dtl_polyline,
    get_bus10e_polyline,
    get_station_by_name,
)
from .geojson_loader import (
    load_geojson_stations,
    get_station_metadata,
    normalize_station_name,
    compute_polygon_centroid,
)
from .door_to_door import (
    get_walking_legs,
    compute_walking_summary,
    calculate_rain_penalty,
)
from .graph_router import (
    StationGraphRouter,
    get_transfer_penalty,
    MRT_LINES,
    INTERCHANGE_TRANSFER_PENALTIES,
)
from .multimodal_router import MultimodalRouter
from .location_resolver import resolve_location, suggest_locations, get_pedestrian_path

__all__ = [
    "ORIGIN_POINT",
    "DESTINATION_POINT",
    "EWL_STATIONS",
    "DTL_STATIONS",
    "BUS_10E_WAYPOINTS",
    "get_ewl_polyline",
    "get_dtl_polyline",
    "get_bus10e_polyline",
    "get_station_by_name",
    "load_geojson_stations",
    "get_station_metadata",
    "normalize_station_name",
    "compute_polygon_centroid",
    "get_walking_legs",
    "compute_walking_summary",
    "calculate_rain_penalty",
    "StationGraphRouter",
    "get_transfer_penalty",
    "MRT_LINES",
    "INTERCHANGE_TRANSFER_PENALTIES",
    "MultimodalRouter",
    "resolve_location",
    "suggest_locations",
    "get_pedestrian_path",
]
