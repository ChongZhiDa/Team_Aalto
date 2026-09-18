"""
Multimodal route evaluation engine.
Calculates door-to-door transit times, evaluates bypass alternatives,
and structures legs for UI display.
"""

from typing import Dict, Any, List


class MultimodalRouter:
    def __init__(self):
        self.base_ewl_time = 42   # 6m walk + 3m wait + 31m train + 2m walk
        self.base_dtl_time = 44   # 5m walk + 3m wait + 31m train + 5m walk
        self.base_bus_time = 45   # 4m walk + 38m bus + 3m walk

    def compute_ewl_journey(self, delay_minutes: int, crowd_level: str, disrupted_stations: List[str]) -> Dict[str, Any]:
        total_time = self.base_ewl_time + delay_minutes
        arr_hour = 7 + (40 + total_time) // 60
        arr_min = (40 + total_time) % 60
        arrival_str = f"{arr_hour:02d}:{arr_min:02d} AM"

        return {
            "id": "primary_ewl",
            "title": "East-West Line (Direct)",
            "transit_type": "Train (MRT)",
            "line": "EWL",
            "total_duration_min": total_time,
            "estimated_arrival": arrival_str,
            "delay_minutes": delay_minutes,
            "status": f"Delayed (+{delay_minutes}m)" if delay_minutes > 0 else "Normal",
            "crowd_level": crowd_level,
            "disrupted_stations": disrupted_stations,
            "is_recommended": delay_minutes < 15,
            "legs": [
                {"mode": "WALK", "name": "Walk from Home to Tampines EWL", "duration": "6 min", "distance": "520m"},
                {"mode": "TRAIN", "name": "EWL: Tampines (EW2) to Raffles Place (EW14)", "duration": f"{31 + delay_minutes} min", "stops": 12},
                {"mode": "WALK", "name": "Walk to One Raffles Place Office", "duration": "2 min", "distance": "120m"},
            ]
        }

    def compute_dtl_bypass(self, crowd_level: str, is_active_bypass: bool) -> Dict[str, Any]:
        total_time = self.base_dtl_time
        arr_hour = 7 + (40 + total_time) // 60
        arr_min = (40 + total_time) % 60
        arrival_str = f"{arr_hour:02d}:{arr_min:02d} AM"

        return {
            "id": "bypass_dtl",
            "title": "Downtown Line Bypass (Recommended)",
            "transit_type": "Train (MRT)",
            "line": "DTL",
            "total_duration_min": total_time,
            "estimated_arrival": arrival_str,
            "delay_minutes": 0,
            "status": "Fastest Reliable Route",
            "crowd_level": crowd_level,
            "disrupted_stations": [],
            "is_recommended": is_active_bypass,
            "legs": [
                {"mode": "WALK", "name": "Walk to Tampines Downtown MRT (DT32)", "duration": "5 min", "distance": "450m"},
                {"mode": "TRAIN", "name": "DTL: Tampines to Telok Ayer (DT18)", "duration": "34 min", "stops": 14},
                {"mode": "WALK", "name": "Sheltered walk via Cross St to Raffles Place", "duration": "5 min", "distance": "410m"},
            ]
        }

    def compute_bus_bypass(self) -> Dict[str, Any]:
        total_time = self.base_bus_time
        arr_hour = 7 + (40 + total_time) // 60
        arr_min = (40 + total_time) % 60
        arrival_str = f"{arr_hour:02d}:{arr_min:02d} AM"

        return {
            "id": "bypass_bus10e",
            "title": "Express Bus 10e (Direct Expressway)",
            "transit_type": "Bus",
            "line": "10e",
            "total_duration_min": total_time,
            "estimated_arrival": arrival_str,
            "delay_minutes": 0,
            "status": "Guaranteed Seat (Load: SEA)",
            "crowd_level": "l",
            "disrupted_stations": [],
            "is_recommended": False,
            "legs": [
                {"mode": "WALK", "name": "Walk to Tampines Ave 7 (Bus Stop 76239)", "duration": "4 min", "distance": "320m"},
                {"mode": "BUS", "name": "Express Bus 10e via ECP to Fullerton Sq", "duration": "38 min", "stops": 6},
                {"mode": "WALK", "name": "Walk to One Raffles Place", "duration": "3 min", "distance": "220m"},
            ]
        }

