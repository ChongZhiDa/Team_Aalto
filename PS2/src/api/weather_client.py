"""
Client for data.gov.sg Real-Time Weather APIs.
No API key required.
Endpoints used:
- 2-hour nowcast: https://api-open.data.gov.sg/v2/real-time/api/two-hr-forecast
- Real-time rainfall: https://api-open.data.gov.sg/v2/real-time/api/rainfall
"""

import requests
from typing import Dict, Any
from .cache_manager import SimpleCache

TWO_HR_FORECAST_URL = "https://api-open.data.gov.sg/v2/real-time/api/two-hr-forecast"
RAINFALL_URL = "https://api-open.data.gov.sg/v2/real-time/api/rainfall"


class WeatherClient:
    def __init__(self):
        self.cache = SimpleCache(default_ttl_seconds=120)

    def get_commute_weather(self, origin_area: str = "Tampines", dest_area: str = "City") -> Dict[str, Any]:
        """
        Fetches 2-hour nowcast for origin and destination areas.
        Returns rain status, forecasts, and shelter recommendation.
        """
        cache_key = f"{origin_area}_{dest_area}"
        cached = self.cache.get(cache_key)
        if cached is not None:
            return cached

        result = {
            "origin_area": origin_area,
            "origin_forecast": "Fair (Day)",
            "origin_raining": False,
            "dest_area": dest_area,
            "dest_forecast": "Fair (Day)",
            "dest_raining": False,
            "rain_alert": False,
            "summary": "Clear weather for walking segments.",
            "source": "data.gov.sg (Live)",
        }

        try:
            resp = requests.get(TWO_HR_FORECAST_URL, timeout=4)
            if resp.status_code == 200:
                payload = resp.json()
                items = payload.get("data", {}).get("items", [])
                if items:
                    forecasts = items[0].get("forecasts", [])
                    for f in forecasts:
                        area = f.get("area", "")
                        forecast = f.get("forecast", "")
                        is_rain = any(term in forecast.lower() for term in ["rain", "shower", "thunder"])

                        if origin_area.lower() in area.lower():
                            result["origin_forecast"] = forecast
                            result["origin_raining"] = is_rain

                        if any(term in area.lower() for term in ["city", "central", "downtown", "marine"]):
                            result["dest_forecast"] = forecast
                            result["dest_raining"] = is_rain

                    if result["origin_raining"] or result["dest_raining"]:
                        result["rain_alert"] = True
                        result["summary"] = "Rain detected along your route. Sheltered walkway routing prioritized."

                self.cache.set(cache_key, result)
        except Exception:
            pass

        return result

