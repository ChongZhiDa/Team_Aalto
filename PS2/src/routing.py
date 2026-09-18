"""Backward-compatible re-export. Code now lives in src.routing package."""
from .routing.coordinates import (
    ORIGIN_POINT,
    DESTINATION_POINT,
    EWL_STATIONS,
    DTL_STATIONS,
    BUS_10E_WAYPOINTS,
    get_ewl_polyline,
    get_dtl_polyline,
    get_bus10e_polyline,
)
from .routing.door_to_door import get_walking_legs
from .routing.multimodal_router import MultimodalRouter

__all__ = [
    "ORIGIN_POINT",
    "DESTINATION_POINT",
    "EWL_STATIONS",
    "DTL_STATIONS",
    "BUS_10E_WAYPOINTS",
    "get_ewl_polyline",
    "get_dtl_polyline",
    "get_bus10e_polyline",
    "get_walking_legs",
    "MultimodalRouter",
]
