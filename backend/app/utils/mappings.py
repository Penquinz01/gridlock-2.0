"""
Mappings — Encoded integers ↔ human-readable labels.

These are placeholder mappings based on data exploration.
Update with actual labels from the original dataset if available.
"""

EVENT_TYPE = {
    0: "Minor Incident",
    1: "Major Incident",
}

EVENT_CAUSE = {
    0: "Rash Driving",
    1: "Signal Jumping",
    2: "Overspeeding",
    3: "Wrong Side Driving",
    4: "Drunk Driving",
    5: "Distracted Driving",
    6: "Poor Road Condition",
    7: "Vehicle Breakdown",
    8: "Weather Related",
    9: "Pedestrian Error",
    10: "Overloading",
    11: "Tyre Burst",
    12: "Brake Failure",
    13: "Lane Changing",
    14: "Rear End Collision",
    15: "Head On Collision",
    16: "Side Collision",
}

VEHICLE_TYPE = {
    0: "Two Wheeler",
    1: "Auto Rickshaw",
    2: "Car/Sedan",
    3: "SUV/MUV",
    4: "Taxi/Cab",
    5: "Bus",
    6: "Mini Truck",
    7: "Truck",
    8: "Tanker",
    9: "Trailer",
}

CORRIDOR = {
    0: "Hosur Road", 1: "Tumkur Road", 2: "Bellary Road",
    3: "Old Madras Road", 4: "Mysore Road", 5: "Bannerghatta Road",
    6: "Sarjapur Road", 7: "Whitefield Road", 8: "Airport Road",
    9: "Kanakapura Road", 10: "Magadi Road", 11: "Hennur Road",
    12: "Old Airport Road", 13: "Koramangala Inner Ring Road",
    14: "Marathahalli Bridge", 15: "Hebbal Flyover",
    16: "Silk Board Junction", 17: "KR Puram Bridge",
    18: "Yeshwanthpur Circle", 19: "Outer Ring Road",
    20: "NICE Road", 21: "Ring Road",
}

PRIORITY = {
    0: "LOW",
    1: "HIGH",
}

ROAD_CLOSURE = {
    0: "Not Required",
    1: "Required",
}


def get_label(mapping: dict, code: int, default: str = "Unknown") -> str:
    """Get human-readable label for an encoded integer."""
    return mapping.get(code, default)
