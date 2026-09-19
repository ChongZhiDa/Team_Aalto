"""
Disruption scenarios and replay engine for PS2 hackathon evaluation.
Allows judges to evaluate StationBuddy under:
1. Normal commute (noise filter suppresses minor headways)
2. Major EWL track fault (triggers proactive DTL bypass & AI advice synthesis)
3. Monsoon rain & crowd surge (PCDForecast high crowd pre-emption & sheltered linkways)
"""

from typing import Dict, Any, List

SCENARIO_NORMAL = "normal"
SCENARIO_EWL_FAULT = "ewl_fault"
SCENARIO_WEATHER_SURGE = "weather_surge"
SCENARIO_LIVE = "live"

SCENARIOS: Dict[str, Dict[str, Any]] = {
    SCENARIO_NORMAL: {
        "id": SCENARIO_NORMAL,
        "name": "Normal Morning (07:20 AM)",
        "badge": "Simulated Replay",
        "description": "Clean morning commute. Minor 2-minute train headway variance. App stays quiet and unobtrusive.",
        "simulated_time": "07:20 AM",
        "alerts": {
            "Status": 1,
            "AffectedSegments": [],
            "Message": [
                {
                    "Content": "[SMRT] Train services on all lines are operating normally. Station staff are available if you require assistance. Have a safe journey.",
                    "CreatedDate": "2026-09-18 07:05:00"
                }
            ]
        },
        "crowd_levels": {
            "EW2": "m",   # Tampines: Moderate
            "EW8": "m",   # Paya Lebar: Moderate
            "EW14": "l",  # Raffles Place: Low
            "DT32": "l",  # Tampines DTL: Low
            "DT18": "l",  # Telok Ayer: Low
            "NE17": "l",  # Punggol: Low
            "CC23": "l",  # one-north: Low
            "EW9": "l",   # Bedok: Low
            "EW16": "l",  # Outram Park: Low
        },
        "pcd_forecast": [
            {"Station": "EW2", "StartTime": "07:30", "EndTime": "08:00", "CrowdLevel": "l"},
            {"Station": "EW2", "StartTime": "08:00", "EndTime": "08:30", "CrowdLevel": "m"},
            {"Station": "EW8", "StartTime": "08:00", "EndTime": "08:30", "CrowdLevel": "m"},
            {"Station": "EW14", "StartTime": "08:00", "EndTime": "08:30", "CrowdLevel": "l"},
        ],
        "weather": {
            "origin_forecast": "Fair (Day)",
            "origin_raining": False,
            "dest_forecast": "Partly Cloudy",
            "dest_raining": False,
            "rain_alert": False,
            "summary": "Clear conditions for walking legs.",
        },
        "delay_minutes": 2,
    },
    SCENARIO_EWL_FAULT: {
        "id": SCENARIO_EWL_FAULT,
        "name": "Whole EWL Line Failure (+25 min)",
        "badge": "Disruption Scenario",
        "description": "The entire East-West Line is unavailable. Scheduled EWL commutes receive an alternative route with updated departure and arrival times.",
        "simulated_time": "07:20 AM",
        "whole_line_failure": True,
        "disrupted_line": "EWL",
        "alerts": {
            "Status": 2,
            "AffectedSegments": [
                {
                    "Line": "EWL",
                    "Direction": "Both",
                    "Stations": "EW5,EW6,EW7,EW8,EW9,EW10,EW11,EW12",
                    "FreePublicBus": "Available at bus stops between Bedok and Bugis",
                    "FreeMRTShuttle": "Operating between Tanah Merah and City Hall",
                    "MRTShuttleDirection": "Both"
                }
            ],
            "Message": [
                {
                    "Content": "[SMRT] EWL Update: The East-West Line is unavailable across the whole line. Please use alternative MRT or bus services and allow additional travel time.",
                    "CreatedDate": "2026-09-18 07:14:22"
                }
            ]
        },
        "disrupted_stations": ["EW5", "EW6", "EW7", "EW8", "EW9", "EW10", "EW11", "EW12"],
        "crowd_levels": {
            "EW2": "h",   # Tampines: High (trains held back)
            "EW8": "h",   # Paya Lebar: Severe crush
            "EW14": "m",  # Raffles Place
            "DT32": "l",  # Tampines DTL: Low (clear bypass!)
            "DT18": "l",  # Telok Ayer: Low
        },
        "pcd_forecast": [
            {"Station": "EW2", "StartTime": "07:30", "EndTime": "08:00", "CrowdLevel": "h"},
            {"Station": "EW2", "StartTime": "08:00", "EndTime": "08:30", "CrowdLevel": "h"},
            {"Station": "EW8", "StartTime": "08:00", "EndTime": "08:30", "CrowdLevel": "h"},
        ],
        "weather": {
            "origin_forecast": "Cloudy",
            "origin_raining": False,
            "dest_forecast": "Cloudy",
            "dest_raining": False,
            "rain_alert": False,
            "summary": "Dry weather along corridor.",
        },
        "delay_minutes": 25,
    },
    SCENARIO_WEATHER_SURGE: {
        "id": SCENARIO_WEATHER_SURGE,
        "name": "Monsoon Downpour + Crowd Surge (+16 min)",
        "badge": "Weather & Crowd Alert",
        "description": "Heavy monsoon downpour hits East Singapore. Station platform crowd spikes to High ('h') with train pass-bys. App routes through 100% sheltered linkways.",
        "simulated_time": "07:20 AM",
        "alerts": {
            "Status": 1,
            "AffectedSegments": [],
            "Message": [
                {
                    "Content": "[SMRT] Advisory: Heavy rain islandwide. Please exercise care on slippery platforms and footways. High platform crowd expected at Tampines and Paya Lebar.",
                    "CreatedDate": "2026-09-18 07:10:00"
                }
            ]
        },
        "crowd_levels": {
            "EW2": "h",   # Tampines EWL: Severe crush
            "EW8": "h",   # Paya Lebar: High
            "EW14": "m",
            "DT32": "m",  # Tampines DTL: Moderate
            "DT18": "l",
        },
        "pcd_forecast": [
            {"Station": "EW2", "StartTime": "07:30", "EndTime": "08:00", "CrowdLevel": "m"},
            {"Station": "EW2", "StartTime": "08:00", "EndTime": "08:30", "CrowdLevel": "h"},
            {"Station": "EW8", "StartTime": "08:00", "EndTime": "08:30", "CrowdLevel": "h"},
        ],
        "weather": {
            "origin_forecast": "Heavy Thundery Showers",
            "origin_raining": True,
            "dest_forecast": "Moderate Rain",
            "dest_raining": True,
            "rain_alert": True,
            "summary": "Heavy rain detected. Prioritizing covered linkways & indoor transfers.",
        },
        "delay_minutes": 16,
    }
}


def get_scenario(scenario_id: str) -> Dict[str, Any]:
    return SCENARIOS.get(scenario_id, SCENARIOS[SCENARIO_NORMAL])


def list_scenarios() -> List[Dict[str, Any]]:
    return [
        {
            "id": s["id"],
            "name": s["name"],
            "badge": s["badge"],
            "description": s["description"],
            "simulated_time": s["simulated_time"]
        }
        for s in SCENARIOS.values()
    ]
