"""
Client for OneMap API (Singapore's official spatial mapping & routing platform).
Documentation: https://www.onemap.gov.sg/apidocs/
Teammate C can expand this with their OneMap token for live dynamic routing!
"""

import os
import requests
from typing import Dict, Any, Optional
from .cache_manager import SimpleCache

ONEMAP_BASE_URL = "https://www.onemap.gov.sg/api"


class OneMapClient:
    def __init__(self, email: Optional[str] = None, password: Optional[str] = None):
        self.token = os.getenv("ONEMAP_TOKEN", "")
        self.cache = SimpleCache(default_ttl_seconds=300)

    def search_address(self, query: str) -> Dict[str, Any]:
        """
        Geocodes a search query (e.g. 'Tampines St 21' or 'One Raffles Place').
        GET /common/elastic/search
        """
        cached = self.cache.get(f"search_{query}")
        if cached:
            return cached

        url = f"{ONEMAP_BASE_URL}/common/elastic/search"
        params = {"searchVal": query, "returnGeom": "Y", "getAddrDetails": "Y"}
        try:
            resp = requests.get(url, params=params, timeout=5)
            if resp.status_code == 200:
                data = resp.json()
                self.cache.set(f"search_{query}", data)
                return data
        except Exception:
            pass
        return {"results": []}

    def get_route(self, start_coords: list, end_coords: list, route_type: str = "walk") -> Dict[str, Any]:
        """
        Queries OneMap routing API (walk, drive, cycle, pt).
        """
        # Stub ready for Teammate C to connect live token
        return {
            "status": "ok",
            "start": start_coords,
            "end": end_coords,
            "route_type": route_type,
            "note": "OneMap connector stub ready for live token"
        }

