"""
PCDForecast Pre-emptive Crowd Departure Engine.
Analyzes 30-minute platform crowd forecasts from LTA DataMall (PCDForecast)
to advise commuters to shift their departure time before platform queues escalate.
"""

from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta


STATION_NAMES: Dict[str, str] = {
    "EW2": "Tampines",
    "EW8": "Paya Lebar",
    "EW9": "Bedok",
    "EW14": "Raffles Place",
    "DT32": "Tampines Downtown",
    "DT18": "Telok Ayer",
    "NE17": "Punggol",
    "CC13": "Serangoon",
    "CC23": "one-north",
    "EW16": "Outram Park",
}


def _parse_time_str(time_str: str) -> datetime:
    """Parses '07:40 AM' or '07:40' into a dummy datetime object for time math."""
    clean = time_str.strip().upper()
    try:
        if "AM" in clean or "PM" in clean:
            return datetime.strptime(clean, "%I:%M %p")
        else:
            return datetime.strptime(clean, "%H:%M")
    except ValueError:
        return datetime.strptime("07:40 AM", "%I:%M %p")


def _format_time_str(dt: datetime) -> str:
    """Formats datetime back to '07:30 AM'."""
    return dt.strftime("%I:%M %p")


def evaluate_pcd_forecast(
    forecast_data: Optional[List[Dict[str, Any]]] = None,
    station_code: str = "EW2",
    departure_time: str = "07:40 AM",
    advance_lead_min: int = 10,
    station_name: Optional[str] = None
) -> Dict[str, Any]:
    """
    Evaluates 30-minute crowd forecast for the commuter's boarding station.
    If platform crowd is forecast as High ('h') around peak arrival (e.g. 08:00 AM),
    proactively advises the commuter to leave early (e.g. 07:30 AM) to beat the rush.
    """
    name = station_name or STATION_NAMES.get(station_code, station_code)
    dep_dt = _parse_time_str(departure_time)
    earlier_dt = dep_dt - timedelta(minutes=advance_lead_min)
    earlier_str = _format_time_str(earlier_dt)

    if not forecast_data:
        # Default benign forecast if no data
        return {
            "forecast_detected": False,
            "station_code": station_code,
            "station_name": name,
            "crowd_level": "m",
            "peak_window": None,
            "suggested_departure": departure_time,
            "advance_lead_min": 0,
            "advice": f"Platform crowd at {name} is forecast moderate. Depart on schedule at {departure_time}.",
        }

    # Search for high crowd forecast records matching station
    for item in forecast_data:
        stn = str(item.get("Station", "")).strip().upper()
        if stn == station_code.upper():
            crowd = str(item.get("CrowdLevel", "l")).lower()
            start_time = item.get("StartTime", "08:00")
            end_time = item.get("EndTime", "08:30")

            if crowd == "h":
                # High platform crowd forecast detected!
                advice = (
                    f"Platform at {name} forecasted High crowd ('h') at {start_time} — "
                    f"leave {advance_lead_min} mins early at {earlier_str} to beat the rush."
                )
                return {
                    "forecast_detected": True,
                    "station_code": station_code,
                    "station_name": name,
                    "crowd_level": "h",
                    "peak_window": f"{start_time} - {end_time}",
                    "suggested_departure": earlier_str,
                    "advance_lead_min": advance_lead_min,
                    "advice": advice,
                }

    # If no 'h' crowd was found
    return {
        "forecast_detected": False,
        "station_code": station_code,
        "station_name": name,
        "crowd_level": "l",
        "peak_window": None,
        "suggested_departure": departure_time,
        "advance_lead_min": 0,
        "advice": f"Platform at {name} forecast normal. Regular departure at {departure_time} recommended.",
    }

