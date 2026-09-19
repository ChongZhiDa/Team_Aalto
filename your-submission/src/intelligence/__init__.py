"""
Commuter Intelligence Package:
- personas: Commuter profiles (Rachel, Arjun, Mdm Lim)
- noise_filter: Delay threshold filtering & alert fatigue prevention
- advisor: Actionable one-line recommendation synthesizer & AI summarizer
- crowd_forecast: PCDForecast pre-emptive crowd departure shifting
- scenarios: Disruption replay presets for judging
"""

from .personas import (
    RACHEL_PROFILE,
    ARJUN_PROFILE,
    MDM_LIM_PROFILE,
    ALL_PERSONAS,
    CommuterProfile,
    register_custom_persona,
    update_persona,
    delete_custom_persona,
    save_personas,
    load_personas,
    get_persona,
    list_personas,
    set_active_persona,
    get_active_persona,
)
from .noise_filter import evaluate_noise_filter, UrgencyLevel
from .custom_router import create_custom_user_route
from .custom_route_adapter import custom_route_bp, register_custom_route_adapter
from .advisor import (
    synthesize_actionable_advice,
    build_advisory_llm_prompt,
    local_nlp_summarize,
    extract_notice_entities,
)
from .crowd_forecast import evaluate_pcd_forecast
from .scenarios import (
    get_scenario,
    list_scenarios,
    SCENARIOS,
    SCENARIO_NORMAL,
    SCENARIO_EWL_FAULT,
    SCENARIO_WEATHER_SURGE,
    SCENARIO_LIVE,
)

__all__ = [
    "RACHEL_PROFILE",
    "ARJUN_PROFILE",
    "MDM_LIM_PROFILE",
    "ALL_PERSONAS",
    "CommuterProfile",
    "register_custom_persona",
    "update_persona",
    "delete_custom_persona",
    "save_personas",
    "load_personas",
    "create_custom_user_route",
    "custom_route_bp",
    "register_custom_route_adapter",
    "get_persona",
    "list_personas",
    "set_active_persona",
    "get_active_persona",
    "evaluate_noise_filter",
    "UrgencyLevel",
    "synthesize_actionable_advice",
    "build_advisory_llm_prompt",
    "local_nlp_summarize",
    "extract_notice_entities",
    "evaluate_pcd_forecast",
    "get_scenario",
    "list_scenarios",
    "SCENARIOS",
    "SCENARIO_NORMAL",
    "SCENARIO_EWL_FAULT",
    "SCENARIO_WEATHER_SURGE",
    "SCENARIO_LIVE",
]
