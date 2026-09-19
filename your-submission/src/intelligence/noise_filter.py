"""
Noise filtering and alert threshold logic.
Prevents alert fatigue by distinguishing meaningful delays from operational noise.
"""

from enum import Enum
from typing import Dict, Any


class UrgencyLevel(str, Enum):
    CALM = "CALM"
    ADVISORY = "ADVISORY"
    CRITICAL = "CRITICAL"


def _parse_to_minutes(time_str: str) -> int:
    """Safely converts time string (e.g. '08:45 AM', '08:45', '14:30') to minutes from midnight."""
    s = str(time_str).strip()
    is_pm = "PM" in s.upper()
    is_am = "AM" in s.upper()
    clean = s.upper().replace("AM", "").replace("PM", "").strip()
    parts = clean.split(":")
    h = int(parts[0]) if len(parts) > 0 and parts[0].isdigit() else 8
    m = int(parts[1]) if len(parts) > 1 and parts[1].isdigit() else 45
    if is_pm and h < 12:
        h += 12
    elif is_am and h == 12:
        h = 0
    return h * 60 + m


def evaluate_noise_filter(delay_minutes: int, threshold_minutes: int, estimated_arrival: str, deadline_arrival: str) -> Dict[str, Any]:
    """
    Evaluates whether the current delay crosses the commuter's pain threshold.
    - If delay < threshold AND arrival <= deadline: noise, keep quiet.
    - If delay >= threshold OR arrival > deadline: trigger proactive alert.
    """
    arr_minutes = _parse_to_minutes(estimated_arrival)
    dead_minutes = _parse_to_minutes(deadline_arrival)

    is_late_for_deadline = arr_minutes > dead_minutes
    exceeds_threshold = delay_minutes >= threshold_minutes

    if exceeds_threshold or is_late_for_deadline:
        return {
            "urgency": UrgencyLevel.CRITICAL.value,
            "status_color": "rose",
            "is_delayed": True,
            "notification_action": "PROACTIVE_PUSH_FIRED",
            "reason": "Exceeds delay threshold and risks meeting deadline."
        }
    elif delay_minutes >= (threshold_minutes // 2):
        return {
            "urgency": UrgencyLevel.ADVISORY.value,
            "status_color": "amber",
            "is_delayed": False,
            "notification_action": "STATUS_ONLY",
            "reason": "Minor headway variance detected, on schedule."
        }
    else:
        return {
            "urgency": UrgencyLevel.CALM.value,
            "status_color": "emerald",
            "is_delayed": False,
            "notification_action": "SUPPRESSED",
            "reason": "Delay below 15-minute threshold. Silent mode maintained."
        }

