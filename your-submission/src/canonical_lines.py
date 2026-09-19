"""
Canonical transit line mapping for Singapore MRT/LRT systems.
Normalizes discrepancies between LTA DataMall TrainServiceAlerts,
Station Crowd Density (PCDRealTime / PCDForecast), and General Transit codes.
"""

from typing import Optional, Dict

# Canonical Line Identifiers
LINE_EWL = "EWL"   # East-West Line
LINE_NSL = "NSL"   # North-South Line
LINE_NEL = "NEL"   # North-East Line
LINE_CCL = "CCL"   # Circle Line
LINE_DTL = "DTL"   # Downtown Line
LINE_TEL = "TEL"   # Thomson-East Coast Line
LINE_BPL = "BPL"   # Bukit Panjang LRT
LINE_SKL = "SKL"   # Sengkang LRT
LINE_PGL = "PGL"   # Punggol LRT

# Color mapping for UI visualization (Official LTA colors)
LINE_COLORS: Dict[str, str] = {
    LINE_EWL: "#009645",  # Green
    LINE_NSL: "#D42E12",  # Red
    LINE_NEL: "#702082",  # Purple
    LINE_CCL: "#FA9E0D",  # Orange
    LINE_DTL: "#005EC4",  # Blue
    LINE_TEL: "#9D5B25",  # Brown
    LINE_BPL: "#748477",  # Grey
    LINE_SKL: "#748477",  # Grey
    LINE_PGL: "#748477",  # Grey
    "BUS": "#E02E24",     # LTA Bus Red
    "WALK": "#4A5568",    # Slate Grey (Pedestrian)
}

LINE_NAMES: Dict[str, str] = {
    LINE_EWL: "East-West Line",
    LINE_NSL: "North-South Line",
    LINE_NEL: "North-East Line",
    LINE_CCL: "Circle Line",
    LINE_DTL: "Downtown Line",
    LINE_TEL: "Thomson-East Coast Line",
    LINE_BPL: "Bukkit Panjang LRT",
    LINE_SKL: "Sengkang LRT",
    LINE_PGL: "Punggol LRT",
}

# Mapping from TrainServiceAlerts endpoint line codes to Canonical
ALERTS_TO_CANONICAL: Dict[str, str] = {
    "EWL": LINE_EWL,
    "NSL": LINE_NSL,
    "NEL": LINE_NEL,
    "CCL": LINE_CCL,
    "DTL": LINE_DTL,
    "TEL": LINE_TEL,
    "BPL": LINE_BPL,
    "STL": LINE_SKL,  # TrainServiceAlerts uses STL for Sengkang LRT
    "PTL": LINE_PGL,  # TrainServiceAlerts uses PTL for Punggol LRT
}

# Mapping from PCD (Crowd Density) TrainLine parameter to Canonical
PCD_TO_CANONICAL: Dict[str, str] = {
    "EWL": LINE_EWL,
    "CGL": LINE_EWL,  # Changi branch mapped to EWL
    "NSL": LINE_NSL,
    "NEL": LINE_NEL,
    "CCL": LINE_CCL,
    "CEL": LINE_CCL,  # Circle Line Extension mapped to CCL
    "DTL": LINE_DTL,
    "TEL": LINE_TEL,
    "BPL": LINE_BPL,
    "SLRT": LINE_SKL, # PCD uses SLRT for Sengkang LRT
    "PLRT": LINE_PGL, # PCD uses PLRT for Punggol LRT
}

# Canonical to PCD request parameter
CANONICAL_TO_PCD: Dict[str, str] = {
    LINE_EWL: "EWL",
    LINE_NSL: "NSL",
    LINE_NEL: "NEL",
    LINE_CCL: "CCL",
    LINE_DTL: "DTL",
    LINE_TEL: "TEL",
    LINE_BPL: "BPL",
    LINE_SKL: "SLRT",
    LINE_PGL: "PLRT",
}


def normalize_alert_line(line_code: str) -> str:
    """Normalizes a line code from TrainServiceAlerts to canonical code."""
    cleaned = line_code.strip().upper()
    return ALERTS_TO_CANONICAL.get(cleaned, cleaned)


def normalize_pcd_line(line_code: str) -> str:
    """Normalizes a line code from PCD crowd density endpoints to canonical code."""
    cleaned = line_code.strip().upper()
    return PCD_TO_CANONICAL.get(cleaned, cleaned)


def get_pcd_request_code(canonical_line: str) -> str:
    """Returns the parameter code required by the LTA PCD endpoint."""
    return CANONICAL_TO_PCD.get(canonical_line, canonical_line)

