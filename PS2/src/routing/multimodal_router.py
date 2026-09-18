"""
Multimodal route evaluation engine.
Calculates door-to-door transit times, evaluates bypass alternatives,
incorporates platform transfer penalties and dynamic rain penalties,
and supports arbitrary station routing via the Singapore MRT graph.
"""

from typing import Dict, Any, List, Optional
from .door_to_door import get_walking_legs, compute_walking_summary, calculate_rain_penalty
from .graph_router import StationGraphRouter, get_transfer_penalty


class MultimodalRouter:
    def __init__(self):
        self.base_ewl_time = 42   # 6m walk + 3m wait + 31m train + 2m walk
        self.base_dtl_time = 44   # 5m walk + 3m wait + 31m train + 5m walk
        self.base_bus_time = 45   # 4m walk + 38m bus + 3m walk
        self.graph_router = StationGraphRouter()

    def get_interchange_penalty(self, from_line: str, to_line: str, station: str) -> int:
        """
        Returns interchange platform transfer walking penalty in minutes.
        Bugis (EWL <-> DTL) = 4 min; Outram Park = 4-5 min; City Hall = 2 min (cross-platform).
        """
        return get_transfer_penalty(from_line, to_line, station)

    def compute_walking_summary(self, rain_active: bool = False, corridor: str = "ewl") -> Dict[str, Any]:
        """Returns door-to-door walking analysis comparing dry vs rain penalties."""
        return compute_walking_summary(rain_active=rain_active, corridor=corridor)

    def compute_ewl_journey(
        self,
        delay_minutes: int,
        crowd_level: str,
        disrupted_stations: List[str],
        rain_active: bool = False
    ) -> Dict[str, Any]:
        walk_summary = compute_walking_summary(rain_active=rain_active, corridor="ewl")
        rain_delay = int(round(walk_summary["rain_delay_min"]))
        total_time = self.base_ewl_time + delay_minutes + rain_delay

        arr_hour = 7 + (40 + total_time) // 60
        arr_min = (40 + total_time) % 60
        arrival_str = f"{arr_hour:02d}:{arr_min:02d} AM"

        # Walking leg durations adjusted for rain
        walk_home_min = 6 + int(round(calculate_rain_penalty(6, 80, rain_active)))
        walk_desk_min = 2  # 100% sheltered, 0 penalty

        status_str = f"Delayed (+{delay_minutes}m)" if delay_minutes > 0 else "Normal"
        if rain_active and rain_delay > 0:
            status_str += f" | Rain slowdown (+{rain_delay}m)"

        return {
            "id": "primary_ewl",
            "title": "East-West Line (Direct)",
            "transit_type": "Train (MRT)",
            "line": "EWL",
            "total_duration_min": total_time,
            "estimated_arrival": arrival_str,
            "delay_minutes": delay_minutes,
            "rain_delay_minutes": rain_delay,
            "status": status_str,
            "crowd_level": crowd_level,
            "disrupted_stations": disrupted_stations,
            "is_recommended": delay_minutes < 15,
            "sheltered_percent": walk_summary["avg_sheltered_percent"],
            "legs": [
                {
                    "mode": "WALK",
                    "name": "Walk from Home to Tampines EWL (80% sheltered)",
                    "duration": f"{walk_home_min} min",
                    "distance": "520m",
                    "sheltered_percent": 80
                },
                {
                    "mode": "TRAIN",
                    "name": "EWL: Tampines (EW2) to Raffles Place (EW14)",
                    "duration": f"{31 + delay_minutes} min",
                    "stops": 12
                },
                {
                    "mode": "WALK",
                    "name": "Walk to One Raffles Place Office (100% sheltered linkway)",
                    "duration": f"{walk_desk_min} min",
                    "distance": "120m",
                    "sheltered_percent": 100
                },
            ]
        }

    def compute_dtl_bypass(
        self,
        crowd_level: str,
        is_active_bypass: bool,
        rain_active: bool = False
    ) -> Dict[str, Any]:
        walk_summary = compute_walking_summary(rain_active=rain_active, corridor="dtl")
        rain_delay = int(round(walk_summary["rain_delay_min"]))
        total_time = self.base_dtl_time + rain_delay

        arr_hour = 7 + (40 + total_time) // 60
        arr_min = (40 + total_time) % 60
        arrival_str = f"{arr_hour:02d}:{arr_min:02d} AM"

        walk_home_min = 5 + int(round(calculate_rain_penalty(5, 90, rain_active)))
        walk_desk_min = 5 + int(round(calculate_rain_penalty(5, 95, rain_active)))

        status_str = "Fastest Reliable Route"
        if rain_active:
            status_str = "High Weather Shield (92% Covered Linkways)"

        return {
            "id": "bypass_dtl",
            "title": "Downtown Line Bypass (Recommended)",
            "transit_type": "Train (MRT)",
            "line": "DTL",
            "total_duration_min": total_time,
            "estimated_arrival": arrival_str,
            "delay_minutes": 0,
            "rain_delay_minutes": rain_delay,
            "status": status_str,
            "crowd_level": crowd_level,
            "disrupted_stations": [],
            "is_recommended": is_active_bypass,
            "sheltered_percent": walk_summary["avg_sheltered_percent"],
            "legs": [
                {
                    "mode": "WALK",
                    "name": "Walk to Tampines Downtown MRT (DT32) (90% sheltered)",
                    "duration": f"{walk_home_min} min",
                    "distance": "450m",
                    "sheltered_percent": 90
                },
                {
                    "mode": "TRAIN",
                    "name": "DTL: Tampines to Telok Ayer (DT18)",
                    "duration": "34 min",
                    "stops": 14
                },
                {
                    "mode": "WALK",
                    "name": "Sheltered walk via Cross St to Raffles Place (95% sheltered)",
                    "duration": f"{walk_desk_min} min",
                    "distance": "410m",
                    "sheltered_percent": 95
                },
            ]
        }

    def compute_bus_bypass(self, rain_active: bool = False) -> Dict[str, Any]:
        walk_summary = compute_walking_summary(rain_active=rain_active, corridor="bus")
        rain_delay = int(round(walk_summary["rain_delay_min"]))
        total_time = self.base_bus_time + rain_delay

        arr_hour = 7 + (40 + total_time) // 60
        arr_min = (40 + total_time) % 60
        arrival_str = f"{arr_hour:02d}:{arr_min:02d} AM"

        walk_home_min = 4 + int(round(calculate_rain_penalty(4, 50, rain_active)))
        walk_desk_min = 3 + int(round(calculate_rain_penalty(3, 60, rain_active)))

        status_str = "Guaranteed Seat (Load: SEA)"
        if rain_active:
            status_str = "⚠️ Heavy Rain on Open Walkways (55% Sheltered)"

        return {
            "id": "bypass_bus10e",
            "title": "Express Bus 10e (Direct Expressway)",
            "transit_type": "Bus",
            "line": "10e",
            "total_duration_min": total_time,
            "estimated_arrival": arrival_str,
            "delay_minutes": 0,
            "rain_delay_minutes": rain_delay,
            "status": status_str,
            "crowd_level": "l",
            "disrupted_stations": [],
            "is_recommended": False,
            "sheltered_percent": walk_summary["avg_sheltered_percent"],
            "legs": [
                {
                    "mode": "WALK",
                    "name": "Walk to Tampines Ave 7 (Bus Stop 76239) (Unsheltered)",
                    "duration": f"{walk_home_min} min",
                    "distance": "320m",
                    "sheltered_percent": 50
                },
                {
                    "mode": "BUS",
                    "name": "Express Bus 10e via ECP to Fullerton Sq",
                    "duration": "38 min",
                    "stops": 6
                },
                {
                    "mode": "WALK",
                    "name": "Walk to One Raffles Place",
                    "duration": f"{walk_desk_min} min",
                    "distance": "220m",
                    "sheltered_percent": 60
                },
            ]
        }

    def route_arbitrary_commute(
        self,
        origin_station: str,
        dest_station: str,
        rain_active: bool = False,
        disrupted_line: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Routes arbitrary journeys across the Singapore MRT graph (Issue 2).
        Returns total transit time, interchange platform transfer penalties,
        and turn-by-turn hops.
        """
        path = self.graph_router.find_path(
            origin=origin_station,
            destination=dest_station,
            disrupted_line=disrupted_line
        )
        if not path:
            return None

        train_min = int(round(path["total_train_min"]))
        walk_min = 8 + (3 if rain_active else 0)  # Default 4m origin walk + 4m dest walk
        total_time = train_min + walk_min

        arr_hour = 8 + (total_time) // 60
        arr_min = (total_time) % 60
        arrival_str = f"{arr_hour:02d}:{arr_min:02d} AM"

        # Build turn-by-turn legs
        legs: List[Dict[str, Any]] = [
            {
                "mode": "WALK",
                "name": f"Walk to {origin_station.title()} MRT",
                "duration": f"{4 + (2 if rain_active else 0)} min",
                "distance": "350m",
                "sheltered_percent": 75
            }
        ]

        # Group consecutive segments on same line
        if path["segments"]:
            current_line = path["segments"][0]["line"]
            start_stn = path["segments"][0]["from_station"]
            hop_count = 0

            for i, seg in enumerate(path["segments"]):
                if seg["line"] != current_line:
                    end_stn = path["segments"][i - 1]["to_station"]
                    legs.append({
                        "mode": "TRAIN",
                        "name": f"{current_line}: {start_stn.title()} to {end_stn.title()}",
                        "duration": f"{int(round(hop_count * 2.3))} min",
                        "stops": hop_count
                    })
                    # Add interchange transfer leg
                    penalty = seg["transfer_penalty_applied"]
                    legs.append({
                        "mode": "WALK",
                        "name": f"Interchange walk at {end_stn.title()} ({current_line} -> {seg['line']})",
                        "duration": f"{penalty} min",
                        "distance": "180m",
                        "sheltered_percent": 100
                    })
                    current_line = seg["line"]
                    start_stn = end_stn
                    hop_count = 1
                else:
                    hop_count += 1

            # Final line segment
            last_stn = path["segments"][-1]["to_station"]
            legs.append({
                "mode": "TRAIN",
                "name": f"{current_line}: {start_stn.title()} to {last_stn.title()}",
                "duration": f"{int(round(hop_count * 2.3))} min",
                "stops": hop_count
            })

        legs.append({
            "mode": "WALK",
            "name": f"Walk from {dest_station.title()} to Final Destination",
            "duration": f"{4 + (1 if rain_active else 0)} min",
            "distance": "320m",
            "sheltered_percent": 85
        })

        lines_str = " -> ".join(path["lines"])
        return {
            "id": "arbitrary_route",
            "title": f"{origin_station.title()} to {dest_station.title()} ({lines_str})",
            "transit_type": "Train (MRT)",
            "line": path["lines"][0] if path["lines"] else "MRT",
            "lines_used": path["lines"],
            "total_duration_min": total_time,
            "estimated_arrival": arrival_str,
            "delay_minutes": 0,
            "status": f"{path['hops']} MRT stops, {path['transfers']} transfer(s)",
            "crowd_level": "m",
            "disrupted_stations": [],
            "is_recommended": True,
            "sheltered_percent": 80,
            "legs": legs
        }
