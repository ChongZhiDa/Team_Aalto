"""Backward-compatible re-export. Code now lives in src.api.weather_client."""
from .api.weather_client import WeatherClient
__all__ = ["WeatherClient"]
