"""
API client package for external data sources:
- LTA DataMall (train alerts, crowd density, bus arrivals)
- data.gov.sg (real-time weather nowcast, rainfall)
- OneMap (geocoding, transit routing)
"""

from .datamall_client import DataMallClient
from .weather_client import WeatherClient
from .onemap_client import OneMapClient
from .cache_manager import SimpleCache

__all__ = ["DataMallClient", "WeatherClient", "OneMapClient", "SimpleCache"]

