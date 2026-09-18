"""
Multimodal route evaluation engine.
Calculates door-to-door transit times, evaluates bypass alternatives,
incorporates platform transfer penalties and dynamic rain penalties,
and supports arbitrary station routing via the Singapore MRT graph.
"""

from typing import Dict, Any, List, Optional
from .door_to_door import get_walking_legs, compute_walking_summary, calculate_rain_penalty
from .graph_router import StationGraphRouter, get_transfer_penalty
from .location_resolver import resolve_location


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

    def compute_arjun_journey(self, rain_active: bool = False, delay_minutes: int = 0) -> Dict[str, Any]:
        """
        Arjun's persona journey: Punggol to one-north (multimodal cycling + transit).
        Optimizes for comfort, cycling path access, and crowd avoidance.
        """
        if rain_active:
            # When raining, cycling is replaced by sheltered LRT / walk to avoid getting soaked
            first_leg = {
                "mode": "WALK",
                "name": "Sheltered walk to Coral Edge LRT (PE3) (Rain Mode)",
                "duration": "7 min",
                "distance": "400m",
                "sheltered_percent": 90
            }
            first_leg_min = 7
            weather_note = "Rain Shield: Swapped open cycling to sheltered LRT linkway"
        else:
            first_leg = {
                "mode": "CYCLE",
                "name": "Cycle via Punggol Park Connector (CyclingPath) to Punggol MRT",
                "duration": "4 min",
                "distance": "950m",
                "sheltered_percent": 30
            }
            first_leg_min = 4
            weather_note = "Good Weather: 950m cycling leg on dedicated park connector"

        # Train: NEL Punggol -> Serangoon (14m) + Transfer (4m) + CCL Serangoon -> one-north (18m)
        train_min = 36 + delay_minutes
        last_leg_min = 4
        total_time = first_leg_min + train_min + last_leg_min

        arr_hour = 8 + (total_time) // 60
        arr_min = (total_time) % 60

        return {
            "id": "arjun_multimodal",
            "persona": "Arjun (Flexible, Multimodal Cyclist)",
            "title": "Cycle + NEL/CCL Train to one-north",
            "transit_type": "Cycle + Train",
            "total_duration_min": total_time,
            "estimated_arrival": f"{arr_hour:02d}:{arr_min:02d} AM",
            "delay_minutes": delay_minutes,
            "status": weather_note,
            "crowd_level": "m",
            "disrupted_stations": [],
            "is_recommended": True,
            "cycling_enabled": not rain_active,
            "bicycle_parking_available": True,
            "legs": [
                first_leg,
                {"mode": "TRAIN", "name": "NEL: Punggol (NE17) to Serangoon (NE12)", "duration": "14 min", "stops": 6},
                {"mode": "WALK", "name": "Platform Transfer at Serangoon (NEL -> CCL)", "duration": "4 min", "distance": "160m", "sheltered_percent": 100},
                {"mode": "TRAIN", "name": "CCL: Serangoon (CC13) to one-north (CC23)", "duration": "18 min", "stops": 8},
                {"mode": "WALK", "name": "Walk from one-north MRT Exit A to Biopolis Desk", "duration": f"{last_leg_min} min", "distance": "350m", "sheltered_percent": 95},
            ]
        }

    def compute_mdm_lim_journey(
        self,
        rain_active: bool = False,
        lift_outages: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Mdm Lim's persona journey: Bedok to SGH Outram Park (Accessibility & Step-Free).
        Slow walking speed, lift maintenance detection, and sheltered walkway priority.
        """
        outages = [o.upper() for o in (lift_outages or [])]
        outram_lift_down = any("OUTRAM" in o for o in outages)

        # Walking at 0.85 m/s (slower speed)
        walk_home_min = 9 + (2 if rain_active else 0)
        train_min = 28  # Bedok to Outram Park direct (11 stops)
        walk_sgh_min = 6 + (4 if outram_lift_down else 0)

        total_time = walk_home_min + train_min + walk_sgh_min
        arr_hour = 8 + (total_time) // 60
        arr_min = (total_time) % 60

        if outram_lift_down:
            accessibility_status = "Lift out of service at Outram Park Exit F - rerouted to ramp at Exit A (+4 min)"
            exit_name = "Walk via Exit A Ramp (Step-free detour) to SGH Medical Centre"
        else:
            accessibility_status = "100% Step-free route: Lifts active at Bedok & Outram Park"
            exit_name = "Walk via Exit F Lift Connector directly into SGH Medical Centre"

        return {
            "id": "mdm_lim_accessibility",
            "persona": "Mdm Lim (Accessibility-Constrained)",
            "title": "East-West Line (Step-Free Direct to SGH)",
            "transit_type": "Train (Step-Free)",
            "line": "EWL",
            "total_duration_min": total_time,
            "estimated_arrival": f"{arr_hour:02d}:{arr_min:02d} AM",
            "delay_minutes": 0,
            "status": accessibility_status,
            "crowd_level": "l",
            "step_free_certified": True,
            "has_lift_alert": outram_lift_down,
            "is_recommended": True,
            "sheltered_percent": 95,
            "legs": [
                {
                    "mode": "WALK",
                    "name": "Slow walk via covered linkway to Bedok MRT Lift Entrance",
                    "duration": f"{walk_home_min} min",
                    "distance": "450m",
                    "sheltered_percent": 95,
                    "step_free": True
                },
                {
                    "mode": "TRAIN",
                    "name": "EWL: Bedok (EW5) to Outram Park (EW16) [Direct, No Transfers]",
                    "duration": "28 min",
                    "stops": 11,
                    "step_free": True
                },
                {
                    "mode": "WALK",
                    "name": exit_name,
                    "duration": f"{walk_sgh_min} min",
                    "distance": "250m",
                    "sheltered_percent": 100,
                    "step_free": True
                },
            ]
        }

    def route_door_to_door(
        self,
        origin_query: str,
        dest_query: str,
        rain_active: bool = False,
        disrupted_line: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Full door-to-door routing for any text query (landmarks, addresses,
        neighbourhoods, MRT station names with or without 'MRT').

        Fuzzy-resolves origin and destination to the nearest MRT station using
        location_resolver, then computes the graph-based MRT journey with
        realistic first/last-mile walk legs and rain penalties.

        Args:
            origin_query: Raw text for origin (e.g. "NUS", "Tampines Mall", "jurong east mrt")
            dest_query:   Raw text for destination (e.g. "SGH", "Marina Bay Sands")
            rain_active:  True if rain is active (adds unsheltered walk penalties)
            disrupted_line: MRT line to avoid (e.g. "EWL")

        Returns:
            Route dict with resolved locations, legs, timing, and unresolved error info.
        """
        all_stations = self.graph_router.get_all_station_names()

        # --- Resolve locations ---
        origin_resolved = resolve_location(origin_query, all_stations)
        dest_resolved = resolve_location(dest_query, all_stations)

        errors: List[str] = []
        if not origin_resolved:
            errors.append(f"Could not find '{origin_query}'. Try a station name or landmark.")
        if not dest_resolved:
            errors.append(f"Could not find '{dest_query}'. Try a station name or landmark.")
        if errors:
            return {
                "id": "door_to_door_error",
                "error": True,
                "messages": errors,
                "origin_query": origin_query,
                "dest_query": dest_query,
            }

        origin_station = origin_resolved["station"]
        dest_station = dest_resolved["station"]

        # Identical station: same-station journey
        if origin_station.lower() == dest_station.lower():
            walk_min = origin_resolved["walk_min"] + dest_resolved["walk_min"]
            return {
                "id": "door_to_door_same_area",
                "title": f"{origin_resolved['display']} to {dest_resolved['display']}",
                "transit_type": "Walk",
                "origin_resolved": origin_resolved,
                "dest_resolved": dest_resolved,
                "total_duration_min": walk_min,
                "estimated_arrival": "~same area",
                "status": f"Both locations served by {origin_station} - walking only",
                "legs": [
                    {
                        "mode": "WALK",
                        "name": f"Walk from {origin_resolved['display']} to {origin_station} MRT",
                        "duration": f"{origin_resolved['walk_min']} min",
                        "distance": f"{origin_resolved['walk_m']}m",
                        "sheltered_percent": 75,
                    },
                    {
                        "mode": "WALK",
                        "name": f"Walk from {dest_station} MRT to {dest_resolved['display']}",
                        "duration": f"{dest_resolved['walk_min']} min",
                        "distance": f"{dest_resolved['walk_m']}m",
                        "sheltered_percent": 75,
                    },
                ],
                "is_recommended": True,
                "error": False,
            }

        # --- Graph routing ---
        path = self.graph_router.find_path(
            origin=origin_station,
            destination=dest_station,
            disrupted_line=disrupted_line,
        )
        if not path:
            return {
                "id": "door_to_door_error",
                "error": True,
                "messages": [f"No MRT path found from {origin_station} to {dest_station}."],
                "origin_query": origin_query,
                "dest_query": dest_query,
            }

        # --- Rain penalty on first/last mile walks ---
        rain_origin_add = round(origin_resolved["walk_min"] * 0.4) if rain_active else 0
        rain_dest_add = round(dest_resolved["walk_min"] * 0.4) if rain_active else 0

        walk_origin_min = origin_resolved["walk_min"] + rain_origin_add
        walk_dest_min = dest_resolved["walk_min"] + rain_dest_add
        train_min = int(round(path["total_train_min"]))
        total_min = walk_origin_min + train_min + walk_dest_min

        arr_hour = 8 + total_min // 60
        arr_min_val = total_min % 60
        ampm = "AM" if arr_hour < 12 else "PM"
        arr_hour_disp = arr_hour if arr_hour <= 12 else arr_hour - 12
        arrival_str = f"{arr_hour_disp:02d}:{arr_min_val:02d} {ampm}"

        # --- Build legs ---
        legs: List[Dict[str, Any]] = [
            {
                "mode": "WALK",
                "name": f"Walk from {origin_resolved['display']} to {origin_station} MRT"
                        + (" (rain - add time)" if rain_origin_add else ""),
                "duration": f"{walk_origin_min} min",
                "distance": f"{origin_resolved['walk_m']}m",
                "sheltered_percent": 70,
                "rain_delay_min": rain_origin_add,
            }
        ]

        # Train legs (grouped by line with interchange walk legs)
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
                        "stops": hop_count,
                    })
                    penalty = seg["transfer_penalty_applied"]
                    legs.append({
                        "mode": "WALK",
                        "name": f"Interchange transfer at {end_stn.title()} ({current_line} -> {seg['line']})",
                        "duration": f"{penalty} min",
                        "distance": "180m",
                        "sheltered_percent": 100,
                    })
                    current_line = seg["line"]
                    start_stn = end_stn
                    hop_count = 1
                else:
                    hop_count += 1

            last_stn = path["segments"][-1]["to_station"]
            legs.append({
                "mode": "TRAIN",
                "name": f"{current_line}: {start_stn.title()} to {last_stn.title()}",
                "duration": f"{int(round(hop_count * 2.3))} min",
                "stops": hop_count,
            })

        legs.append({
            "mode": "WALK",
            "name": f"Walk from {dest_station} MRT to {dest_resolved['display']}"
                    + (" (rain - add time)" if rain_dest_add else ""),
            "duration": f"{walk_dest_min} min",
            "distance": f"{dest_resolved['walk_m']}m",
            "sheltered_percent": 75,
            "rain_delay_min": rain_dest_add,
        })

        lines_str = " -> ".join(path["lines"])

        from .geojson_loader import get_station_metadata
        from .coordinates import get_station_by_name

        route_stations: List[Dict[str, Any]] = []
        route_polyline: List[List[float]] = []

        if path["segments"]:
            first_stn = path["segments"][0]["from_station"]
            first_meta = get_station_metadata(first_stn) or get_station_by_name(first_stn)
            first_coords = first_meta["coords"] if first_meta else [1.3521, 103.8198]
            route_stations.append({
                "name": first_stn.title(),
                "coords": first_coords,
                "line": path["segments"][0]["line"],
            })
            route_polyline.append(first_coords)

            for seg in path["segments"]:
                stn_name = seg["to_station"]
                meta = get_station_metadata(stn_name) or get_station_by_name(stn_name)
                coords = meta["coords"] if meta else [1.3521, 103.8198]
                route_stations.append({
                    "name": stn_name.title(),
                    "coords": coords,
                    "line": seg["line"],
                })
                route_polyline.append(coords)

        if origin_resolved.get("coordinates"):
            route_polyline.insert(0, origin_resolved["coordinates"])
        if dest_resolved.get("coordinates"):
            route_polyline.append(dest_resolved["coordinates"])
        elif "raffles" in dest_resolved.get("display", "").lower() or "cbd" in dest_resolved.get("display", "").lower():
            route_polyline.append([1.2840, 103.8515])

        return {
            "id": "door_to_door",
            "title": f"{origin_resolved['display']} to {dest_resolved['display']}",
            "transit_type": "Train (MRT)" if path["lines"] else "Walk",
            "line": path["lines"][0] if path["lines"] else "MRT",
            "lines_used": path["lines"],
            "total_duration_min": total_min,
            "estimated_arrival": arrival_str,
            "delay_minutes": 0,
            "rain_active": rain_active,
            "status": f"{path['hops']} stops, {path['transfers']} transfer(s) via {lines_str}",
            "origin_resolved": origin_resolved,
            "dest_resolved": dest_resolved,
            "crowd_level": "m",
            "disrupted_stations": [],
            "is_recommended": True,
            "sheltered_percent": 80,
            "error": False,
            "legs": legs,
            "polyline": route_polyline,
            "route_polyline": route_polyline,
            "coordinates": route_polyline,
            "stations": route_stations,
            "route_stations": route_stations,
        }
