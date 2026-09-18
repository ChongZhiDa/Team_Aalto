"""
LTA DataMall API Client.
Interfaces with official Singapore Land Transport Authority endpoints:
- TrainServiceAlerts (Structured train disruptions, bridging buses, shuttles)
- PCDRealTime / PCDForecast (Station crowd densities)
- v3/BusArrival (Bus occupancy / Load: SEA, SDA, LSD)
- v2/FacilitiesMaintenance (MRT station lift maintenance)
"""

import os
import requests
from typing import Dict, Any, List, Optional
from ..canonical_lines import get_pcd_request_code
from .cache_manager import SimpleCache

BASE_URL = "https://datamall2.mytransport.sg/ltaodataservice"


class DataMallClient:
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv("LTA_DATAMALL_KEY", "")
        self.cache = SimpleCache(default_ttl_seconds=60)

    def _get_headers(self) -> Dict[str, str]:
        return {
            "AccountKey": self.api_key,
            "Accept": "application/json",
        }

    def _fetch(self, endpoint: str, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Fetches data from DataMall with caching and graceful fallbacks."""
        cache_key = f"{endpoint}_{str(params)}"
        cached = self.cache.get(cache_key)
        if cached is not None:
            return cached

        if not self.api_key:
            return {"value": [], "status": "no_api_key"}

        try:
            url = f"{BASE_URL}/{endpoint}"
            resp = requests.get(url, headers=self._get_headers(), params=params, timeout=5)
            if resp.status_code == 200:
                data = resp.json()
                self.cache.set(cache_key, data)
                return data
            return {"value": [], "status": f"http_error_{resp.status_code}"}
        except Exception as e:
            return {"value": [], "status": f"exception_{str(e)}"}

    def get_train_service_alerts(self) -> Dict[str, Any]:
        """
        GET /TrainServiceAlerts
        Returns structured disruption info: Status, AffectedSegments, Message.
        """
        data = self._fetch("TrainServiceAlerts")
        if "value" in data and isinstance(data["value"], dict):
            return data["value"]
        return {
            "Status": 1,
            "AffectedSegments": [],
            "Message": []
        }

    def get_pcd_realtime(self, canonical_line: str) -> List[Dict[str, Any]]:
        """
        GET /PCDRealTime?TrainLine=<code>
        Returns list of station crowd levels (l, m, h, NA).
        """
        pcd_code = get_pcd_request_code(canonical_line)
        data = self._fetch("PCDRealTime", {"TrainLine": pcd_code})
        return data.get("value", [])

    def get_pcd_forecast(self, canonical_line: str) -> List[Dict[str, Any]]:
        """
        GET /PCDForecast?TrainLine=<code>
        Returns 30-minute crowd forecast for the line.
        """
        pcd_code = get_pcd_request_code(canonical_line)
        data = self._fetch("PCDForecast", {"TrainLine": pcd_code})
        return data.get("value", [])

    def get_bus_arrival(self, bus_stop_code: str, service_no: Optional[str] = None) -> Dict[str, Any]:
        """
        GET /v3/BusArrival?BusStopCode=<code>
        Returns arrival ETA, Load (SEA, SDA, LSD), and Feature (WAB).
        """
        params = {"BusStopCode": bus_stop_code}
        if service_no:
            params["ServiceNo"] = service_no
        return self._fetch("v3/BusArrival", params)

    def get_facilities_maintenance(self) -> List[Dict[str, Any]]:
        """
        GET /v2/FacilitiesMaintenance
        Returns lift / escalator maintenance status at stations.
        """
        data = self._fetch("v2/FacilitiesMaintenance")
        return data.get("value", [])

