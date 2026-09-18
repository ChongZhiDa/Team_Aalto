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


def evaluate_noise_filter(delay_minutes: int, threshold_minutes: int, estimated_arrival: str, deadline_arrival: str) -> Dict[str, Any]:
    """
    Evaluates whether the current delay crosses the commuter's pain threshold.
    - If delay < threshold AND arrival <= deadline: noise, keep quiet.
    - If delay >= threshold OR arrival > deadline: trigger proactive alert.
    """
    # Parse arrival hour and minute e.g. "08:47 AM"
    parts = estimated_arrival.replace(" AM", "").split(":")
    arr_h, arr_m = int(parts[0]), int(parts[1])

    d_parts = deadline_arrival.replace(" AM", "").split(":")
    dead_h, dead_m = int(d_parts[0]), int(d_parts[1])

    is_late_for_deadline = (arr_h > dead_h) or (arr_h == dead_h and arr_m > dead_m)
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

