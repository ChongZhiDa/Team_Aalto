"""
Commuter Intelligence Package:
- personas: Commuter profiles (Rachel, Arjun, Mdm Lim)
- noise_filter: Delay threshold filtering & alert fatigue prevention
- advisor: Actionable one-line recommendation synthesizer & AI summarizer
- scenarios: Disruption replay presets for judging
"""

from .personas import RACHEL_PROFILE, ALL_PERSONAS, get_persona
from .noise_filter import evaluate_noise_filter, UrgencyLevel
from .advisor import synthesize_actionable_advice
from .scenarios import get_scenario, list_scenarios, SCENARIOS, SCENARIO_NORMAL, SCENARIO_EWL_FAULT, SCENARIO_WEATHER_SURGE

__all__ = [
    "RACHEL_PROFILE",
    "ALL_PERSONAS",
    "get_persona",
    "evaluate_noise_filter",
    "UrgencyLevel",
    "synthesize_actionable_advice",
    "get_scenario",
    "list_scenarios",
    "SCENARIOS",
    "SCENARIO_NORMAL",
    "SCENARIO_EWL_FAULT",
    "SCENARIO_WEATHER_SURGE",
]

