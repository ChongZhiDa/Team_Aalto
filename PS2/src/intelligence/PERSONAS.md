# Customizable commuter profiles

Edit `persona_presets.json` to change default profile values or add a preset.
The file loads when the intelligence package is imported; restart the application
after editing it. Keep the `rachel`, `arjun`, and `mdm_lim` IDs because existing
master-file callers use them. New presets need `is_custom: false`.

The master files (`app.py` and `src/engine.py`) are unchanged. Their existing
persona-specific routing remains in place. Use the intelligence API below for
profile-driven custom routing; these changes do not add a web UI or API endpoint.

## Create, edit, save and reload

Run from the `PS2` directory:

```python
from src.intelligence import (
    register_custom_persona, update_persona, save_personas, load_personas,
    create_custom_user_route,
)

profile = register_custom_persona({
    "template_id": "arjun",  # Optional: inherit any existing profile.
    "name": "Alex",
    "origin": "Jurong East",
    "destination": "Bishan",
    "departure_time": "08:15",
    "deadline_arrival": "09:15",
    "cycling_enabled": False,
    "walking_speed_mps": 1.1,
    "allowed_modes": ["WALK", "TRAIN"],
    "max_walking_distance_m": 1500,
    "max_transfers": 2,
    "crowd_tolerance": "low",
    "rain_shelter_priority": 0.9,
    "requires_step_free": False,
    "requires_lift_monitoring": False,
    "advice_tone": "friendly and reassuring",
    "advice_max_chars": 160,
})

profile = update_persona(profile["id"], {"walking_speed_mps": 1.2})
save_personas("data/my_personas.json")
load_personas("data/my_personas.json")

result = create_custom_user_route(profile=profile, rain_active=True)
if result["status"] == "success":
    print(result["decision"]["one_line_advice"])
else:
    print(result["code"], result["message"])
```

JSON persistence is explicit: call `save_personas` after edits and
`load_personas` to restore them. The saved version-1 file contains a `profiles`
list and can be edited directly. Loading validates every entry before merging
the profiles into the registry. Omitted profiles are retained.

Identical display names receive different IDs. To edit an existing profile,
use `update_persona`; registration never overwrites an existing ID.

## Independent settings

| Setting | Behavior |
| --- | --- |
| `walking_speed_mps`, `cycling_speed_mps` | Recompute movement duration from each leg's distance. |
| `allowed_modes` | Reject routes containing disallowed modes: WALK, TRAIN, CYCLE or BUS. |
| `cycling_enabled`, `avoid_cycling_in_rain` | Use a cycling option when one is supplied and permitted. |
| `max_walking_distance_m`, `max_transfers` | Enforce mandatory limits; `null` means no limit. |
| `requires_step_free` | Require every leg to have verified `step_free: true`. |
| `requires_lift_monitoring` | Require route data with `lifts_operational: true`. |
| `stair_aversion` | Prefer verified step-free candidates; does not imply slower walking or mandatory lift monitoring. |
| `crowd_tolerance` | Rank crowd levels; `high` disables advice to depart early for crowding. |
| `rain_shelter_priority` | Rank sheltered routes during rain, between 0 and 1. |
| `normal_duration_min`, `arrival_buffer_min` | Derive a deadline when one is absent. |
| `proactive_lead_min`, `crowd_advance_lead_min` | Configure pre-departure check timing and crowd-advice lead time. |
| `advice_tone`, `advice_max_chars` | Configure the optional LLM prompt and limit advisory length; minimum 40 characters. |

Speeds must be positive; thresholds and limits must be non-negative.
Time strings support `HH:MM` or `HH:MM AM/PM`. Unknown settings fail validation
so misspelled preferences cannot be silently ignored.

## Router data and limitations

The existing graph router provides a single MRT candidate with estimated walking
distances. Those distances are not address-level measurements. It does not
supply verified cycling paths, lift operation, or accessibility evidence.
Mandatory accessibility requirements therefore return `NO_FEASIBLE_ROUTE`
when the available data cannot verify them.

An injected router may return an `alternatives` list of candidate routes and a
`first_mile_cycle_leg` with a real path and distance. Custom routing filters
mandatory requirements and ranks the remaining candidates by journey duration,
crowding, stair avoidance, and rain shelter. It does not search for additional
paths beyond those the router supplies. Unsupported routes are never replaced
with a fabricated successful journey.

Per-journey overrides do not edit a stored profile. Creating a route leaves
the global active persona unchanged unless `activate_profile=True` is supplied.
Advice names the actual selected route and never assumes that an unknown user
uses Rachel's departure time or Downtown Line bypass.
