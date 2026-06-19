"""
Recommendation Rules — Resource allocation based on risk level.

Simple lookup table. Modify the values here to change recommendations.
"""


RESOURCE_TABLE = {
    "CRITICAL": {
        "officers": 8,
        "barricades": 6,
        "escalation": "DCP",
        "notes": [
            "Activate emergency response protocol",
            "Alert nearby hospitals",
            "Deploy traffic diversion team",
            "Notify senior officers immediately",
        ],
    },
    "HIGH": {
        "officers": 6,
        "barricades": 4,
        "escalation": "ACP",
        "notes": [
            "Deploy traffic diversion team",
            "Alert nearby hospitals",
            "Set up temporary traffic signals",
        ],
    },
    "MEDIUM": {
        "officers": 4,
        "barricades": 2,
        "escalation": "Inspector",
        "notes": [
            "Standard response protocol",
            "Monitor traffic flow",
        ],
    },
    "LOW": {
        "officers": 2,
        "barricades": 0,
        "escalation": "Sub-Inspector",
        "notes": [
            "Monitor situation",
            "File standard report",
        ],
    },
}


# Extra notes added based on specific conditions
CONDITIONAL_NOTES = [
    (lambda i: i.get("requires_road_closure") == 1,
     "Prepare road closure equipment and signage"),

    (lambda i: i.get("event_type") == 1,
     "Prepare for potential media attention"),

    (lambda i: i.get("veh_type") in [7, 8, 9],
     "Request crane/heavy vehicle recovery unit"),
]
