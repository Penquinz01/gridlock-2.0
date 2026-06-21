"""
Risk Rules — All risk scoring logic in one place. Easy to read and tweak.

How it works:
    Each rule is a tuple of (condition_function, points, description).
    The risk engine evaluates ALL rules and sums up the points.
    The total score is capped at 100.
"""


RISK_RULES = [
    # (condition, points, human-readable factor description)
    (lambda i: i["priority"] == 1,
     35, "High priority incident"),

    (lambda i: i["requires_road_closure"] == 1,
     20, "Road closure required"),

    (lambda i: i["hour"] in range(8, 11) or i["hour"] in range(17, 20),
     15, "Peak traffic hour (8-10 AM or 5-7 PM)"),

    (lambda i: i["hour"] in range(22, 24) or i["hour"] in range(0, 5),
     10, "Night-time incident (reduced visibility)"),

    (lambda i: i["event_type"] == 1,
     25, "Major event type"),

    (lambda i: i["veh_type"] in [5, 6, 7, 8, 9],
     10, "Heavy vehicle involved"),

    (lambda i: i["veh_type"] == 0,
     5, "Two-wheeler involved (vulnerable road user)"),
]


def get_risk_level(score: int) -> str:
    """Convert numeric score to risk level label (HIGH or LOW)."""
    if score >= 40:
        return "HIGH"
    return "LOW"

