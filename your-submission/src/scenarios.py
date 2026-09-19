"""Backward-compatible re-export. Code now lives in src.intelligence.scenarios."""
from .intelligence.scenarios import (
    SCENARIO_NORMAL,
    SCENARIO_EWL_FAULT,
    SCENARIO_WEATHER_SURGE,
    SCENARIO_LIVE,
    SCENARIOS,
    get_scenario,
    list_scenarios,
)

__all__ = [
    "SCENARIO_NORMAL",
    "SCENARIO_EWL_FAULT",
    "SCENARIO_WEATHER_SURGE",
    "SCENARIO_LIVE",
    "SCENARIOS",
    "get_scenario",
    "list_scenarios",
]
