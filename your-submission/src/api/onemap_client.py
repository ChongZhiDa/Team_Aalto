"""
Client for OneMap API (Singapore's official spatial mapping & routing platform).
Documentation: https://www.onemap.gov.sg/apidocs/
Supports:
- Live address and postal code search (geocoding)
- Autocomplete and location normalization
- Token authentication (email/password or static ONEMAP_TOKEN)
- Dynamic multi-modal routing (walk, drive, cycle, public transport)
"""

import os
import math
from datetime import datetime
import requests
from typing import Dict, Any, List, Optional, Union, Tuple
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from .cache_manager import SimpleCache

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

ONEMAP_BASE_URL = "https://www.onemap.gov.sg/api"


def decode_polyline(polyline_str: str) -> List[List[float]]:
    """
    Decodes a Google Encoded Polyline string into a list of [lat, lon] coordinates.
    Used for parsing OneMap routing API geometry.
    """
    if not polyline_str:
        return []
    coords: List[List[float]] = []
    index = 0
    lat = 0
    lng = 0
    length = len(polyline_str)
    while index < length:
        shift = 0
        result = 0
        while True:
            byte = ord(polyline_str[index]) - 63
            index += 1
            result |= (byte & 0x1F) << shift
            shift += 5
            if byte < 0x20:
                break
        dlat = ~(result >> 1) if (result & 1) else (result >> 1)
        lat += dlat

        shift = 0
        result = 0
        while True:
            byte = ord(polyline_str[index]) - 63
            index += 1
            result |= (byte & 0x1F) << shift
            shift += 5
            if byte < 0x20:
                break
        dlng = ~(result >> 1) if (result & 1) else (result >> 1)
        lng += dlng

        coords.append([round(lat / 1e5, 5), round(lng / 1e5, 5)])
    return coords


class OneMapClient:
    def __init__(
        self,
        token: Optional[str] = None,
        email: Optional[str] = None,
        password: Optional[str] = None
    ):
        if token is not None:
            self.token = token
        else:
            self.token = os.getenv("ONEMAP_TOKEN", "")
        self.cache = SimpleCache(default_ttl_seconds=300, max_size=1000)

        # Persistent connection pool for fast geocoding and routing
        self.session = requests.Session()
        retries = Retry(
            total=2,
            backoff_factor=0.2,
            status_forcelist=[500, 502, 503, 504],
            raise_on_status=False
        )
        adapter = HTTPAdapter(pool_connections=5, pool_maxsize=10, max_retries=retries)
        self.session.mount("https://", adapter)
        self.session.mount("http://", adapter)

        # If email/password provided or found in environment, authenticate automatically
        user_email = email or os.getenv("ONEMAP_EMAIL", "")
        user_pass = password or os.getenv("ONEMAP_PASSWORD", "")
        if token is None and not self.token and user_email and user_pass:
            self.authenticate(user_email, user_pass)

    def _get_headers(self) -> Dict[str, str]:
        headers: Dict[str, str] = {
            "Accept": "application/json"
        }
        if self.token:
            headers["Authorization"] = self.token
        return headers

    def authenticate(self, email: str, password: str) -> Optional[str]:
        """
        Obtains a bearer token using OneMap registered credentials.
        POST /api/auth/post/getToken
        """
        url = f"{ONEMAP_BASE_URL}/auth/post/getToken"
        payload = {"email": email, "password": password}
        try:
            resp = self.session.post(url, json=payload, timeout=5)
            if resp.status_code == 200:
                data = resp.json()
                token = data.get("access_token")
                if token:
                    self.token = token
                    return token
        except Exception:
            pass
        return None

    def search_address(self, query: str, page_num: int = 1) -> Dict[str, Any]:
        """
        Geocodes a search query or postal code (e.g. '529538', 'Tampines St 21', 'One Raffles Place').
        GET /common/elastic/search
        Cached for 3600 seconds (1 hr) as Singapore building / postal locations are static.
        """
        if not query or not query.strip():
            return {"found": 0, "results": []}

        cleaned_query = query.strip()
        cache_key = f"onemap_search_{cleaned_query}_{page_num}"
        cached = self.cache.get(cache_key)
        if cached is not None:
            return cached

        url = f"{ONEMAP_BASE_URL}/common/elastic/search"
        params = {
            "searchVal": cleaned_query,
            "returnGeom": "Y",
            "getAddrDetails": "Y",
            "pageNum": page_num
        }
        try:
            resp = self.session.get(url, headers=self._get_headers(), params=params, timeout=5)
            if resp.status_code == 200:
                data = resp.json()
                # 1 hour TTL for static location searches
                self.cache.set(cache_key, data, ttl=3600)
                return data
        except Exception:
            pass
        return {"found": 0, "results": []}


    def autocomplete(self, query: str, limit: int = 5) -> List[Dict[str, Any]]:
        """
        Returns clean, structured location suggestions for user inputs / search boxes.
        Each item contains label, building, address, postal, coordinates (lat/lng).
        """
        raw_data = self.search_address(query)
        results = raw_data.get("results", [])
        formatted: List[Dict[str, Any]] = []

        for item in results[:limit]:
            search_val = item.get("SEARCHVAL", "")
            building = item.get("BUILDING", "")
            if building == "NIL":
                building = ""
            postal = item.get("POSTAL", "")
            if postal == "NIL":
                postal = ""
            road_name = item.get("ROAD_NAME", "")
            if road_name == "NIL":
                road_name = ""
            block_no = item.get("BLK_NO", "")
            if block_no == "NIL":
                block_no = ""

            try:
                lat = float(item["LATITUDE"]) if item.get("LATITUDE") not in (None, "NIL", "") else None
                lng = float(item["LONGITUDE"]) if item.get("LONGITUDE") not in (None, "NIL", "") else None
            except (ValueError, TypeError):
                lat, lng = None, None

            # Generate friendly human-readable label
            label = search_val
            if postal:
                label = f"{search_val} (S{postal})"

            formatted.append({
                "label": label,
                "search_val": search_val,
                "building": building,
                "address": item.get("ADDRESS", ""),
                "postal": postal,
                "road_name": road_name,
                "block_no": block_no,
                "latitude": lat,
                "longitude": lng,
                "coords": [lat, lng] if lat is not None and lng is not None else None,
            })

        return formatted

    def search_postal_code(self, postal_code: str) -> Optional[Dict[str, Any]]:
        """
        Direct lookup for a 6-digit Singapore postal code.
        Returns the top matched location dict or None.
        """
        cleaned = postal_code.strip()
        matches = self.autocomplete(cleaned, limit=1)
        if matches:
            return matches[0]
        return None

    def _normalize_coords(self, coords: Union[List[float], Tuple[float, float], str]) -> Tuple[float, float, str]:
        """Normalizes coordinate inputs to (lat, lng, 'lat,lng')."""
        if isinstance(coords, str):
            parts = [float(p.strip()) for p in coords.split(",") if p.strip()]
            return parts[0], parts[1], f"{parts[0]},{parts[1]}"
        elif isinstance(coords, (list, tuple)) and len(coords) >= 2:
            lat = float(coords[0])
            lng = float(coords[1])
            return lat, lng, f"{lat},{lng}"
        raise ValueError(f"Invalid coordinate format: {coords}")

    def get_route(
        self,
        start_coords: Union[List[float], Tuple[float, float], str],
        end_coords: Union[List[float], Tuple[float, float], str],
        route_type: str = "walk",
        mode: str = "TRANSIT",
        date: Optional[str] = None,
        time_str: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Queries OneMap routing API (walk, drive, cycle, pt).
        If live API token is present, calls the official /public/routingsvc/route endpoint.
        Gracefully falls back to structured routing estimates if token or network is unavailable.
        """
        try:
            s_lat, s_lng, start_str = self._normalize_coords(start_coords)
            e_lat, e_lng, end_str = self._normalize_coords(end_coords)
        except Exception as err:
            return {"status": "error", "message": str(err)}

        cache_key = f"route_{start_str}_{end_str}_{route_type}_{mode}_{date}_{time_str}"
        cached = self.cache.get(cache_key)
        if cached is not None:
            return cached

        # Attempt live OneMap Routing API call
        if self.token:
            url = f"{ONEMAP_BASE_URL}/public/routingsvc/route"
            params: Dict[str, Any] = {
                "start": start_str,
                "end": end_str,
                "routeType": route_type,
            }
            if route_type == "pt":
                if mode:
                    params["mode"] = mode
                if date:
                    params["date"] = date
                if time_str:
                    params["time"] = time_str

            try:
                resp = self.session.get(url, headers=self._get_headers(), params=params, timeout=6)
                if resp.status_code == 200:
                    data = resp.json()
                    result = {
                        "status": "ok",
                        "source": "onemap_live",
                        "route_type": route_type,
                        "start": [s_lat, s_lng],
                        "end": [e_lat, e_lng],
                        "data": data,
                    }
                    self.cache.set(cache_key, result)
                    return result
            except Exception:
                pass

        # Robust fallback estimation based on haversine distance & Singapore urban factors
        # Earth radius ~6371km
        dlat = math.radians(e_lat - s_lat)
        dlng = math.radians(e_lng - s_lng)
        a = (
            math.sin(dlat / 2) ** 2
            + math.cos(math.radians(s_lat)) * math.cos(math.radians(e_lat)) * math.sin(dlng / 2) ** 2
        )
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
        straight_dist_m = 6371000 * c

        # Urban detour factor (~1.25x for walkways and roads)
        est_distance_m = int(round(straight_dist_m * 1.25))

        # Speed estimations: Walk = 1.35 m/s (~4.8 km/h), Cycle = 4.2 m/s (~15 km/h), Drive/Bus = 9.0 m/s (~32 km/h)
        speed_mps = 1.35 if route_type == "walk" else (4.2 if route_type == "cycle" else 9.0)
        est_duration_min = max(1, int(round((est_distance_m / speed_mps) / 60)))

        fallback_result = {
            "status": "ok",
            "source": "fallback_model",
            "route_type": route_type,
            "start": [s_lat, s_lng],
            "end": [e_lat, e_lng],
            "total_distance_m": est_distance_m,
            "total_duration_min": est_duration_min,
            "note": "Estimated using Singapore urban routing model (OneMap live token optional)",
        }
        self.cache.set(cache_key, fallback_result)
        return fallback_result

    def get_public_bus_itinerary(
        self,
        start_coords: Union[List[float], Tuple[float, float], str],
        end_coords: Union[List[float], Tuple[float, float], str],
        target_arrival: str = "08:45 AM"
    ) -> Optional[Dict[str, Any]]:
        """
        Retrieves public bus routing between two coordinates via OneMap API.
        Extracts bus service numbers, turn-by-turn legs, total duration, and decoded polylines.
        """
        now = datetime.now()
        date_str = now.strftime("%m-%d-%Y")
        raw = self.get_route(
            start_coords,
            end_coords,
            route_type="pt",
            mode="BUS",
            date=date_str,
            time_str="08:00:00"
        )
        if raw.get("status") != "ok" or not raw.get("data"):
            return None

        data = raw["data"]
        plan = data.get("plan")
        if not plan or not plan.get("itineraries"):
            return None

        itins = plan["itineraries"]
        best_itin = itins[0]

        total_sec = best_itin.get("duration", 0)
        total_min = max(1, round(total_sec / 60))

        bus_services: List[str] = []
        legs: List[Dict[str, Any]] = []
        all_polyline: List[List[float]] = []

        for leg in best_itin.get("legs", []):
            mode = leg.get("mode", "").upper()
            leg_sec = leg.get("duration", 0)
            leg_min = max(1, round(leg_sec / 60))
            dist_m = round(leg.get("distance", 0))

            geom_str = leg.get("legGeometry", {}).get("points", "")
            pts = decode_polyline(geom_str) if geom_str else []
            if pts:
                all_polyline.extend(pts)

            from_name = leg.get("from", {}).get("name", "")
            to_name = leg.get("to", {}).get("name", "")

            if mode == "BUS":
                route_num = str(leg.get("routeShortName") or leg.get("route") or "Bus").strip()
                if route_num and route_num not in bus_services:
                    bus_services.append(route_num)

                legs.append({
                    "mode": "BUS",
                    "name": f"Bus {route_num}: {from_name} to {to_name}",
                    "line": f"Bus {route_num}",
                    "duration": f"{leg_min} min",
                    "distance": f"{dist_m}m",
                    "sheltered_percent": 100,
                    "coords": pts,
                })
            else:
                walk_name = f"Walk to {to_name}" if to_name else "Walk to next transfer"
                legs.append({
                    "mode": "WALK",
                    "name": walk_name,
                    "duration": f"{leg_min} min",
                    "distance": f"{dist_m}m",
                    "sheltered_percent": 70,
                    "coords": pts,
                })

        title = f"Bus {' -> '.join(bus_services)}" if bus_services else "Public Bus Service"
        
        arr_hour = 8 + (total_min // 60)
        arr_min = total_min % 60
        ampm = "AM" if arr_hour < 12 else "PM"
        disp_hour = arr_hour if arr_hour <= 12 else arr_hour - 12
        arrival_str = f"{disp_hour:02d}:{arr_min:02d} {ampm}"

        return {
            "id": "bypass_bus10e",
            "title": title,
            "transit_type": "Public Bus",
            "line": "BUS",
            "lines_used": [f"Bus {s}" for s in bus_services] if bus_services else ["BUS"],
            "total_duration_min": total_min,
            "estimated_arrival": arrival_str,
            "delay_minutes": 0,
            "status": f"{len(bus_services)} bus connection(s) • Surface road transit",
            "crowd_level": "l",
            "is_recommended": False,
            "sheltered_percent": 65,
            "legs": legs,
            "polyline": all_polyline,
            "walking_paths": {},
            "stations": [],
        }

    def close(self) -> None:
        """Closes the underlying HTTP session."""
        self.session.close()


