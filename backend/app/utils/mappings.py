"""
Mappings — Encoded integers ↔ human-readable labels.

These are derived directly from Data.csv using sklearn LabelEncoder
(alphabetical ordering), matching the preprocessing in data_preprocess.ipynb.
"""

# event_type: planned=0, unplanned=1
EVENT_TYPE = {
    0: "Planned",
    1: "Unplanned",
}

# event_cause: alphabetical order from LabelEncoder on actual Data.csv
EVENT_CAUSE = {
    0:  "Debris (capitalised)",   # 'Debris' (capital D — appears as duplicate entry)
    1:  "Fog / Low Visibility",
    2:  "Accident",
    3:  "Congestion",
    4:  "Construction",
    5:  "Debris",
    6:  "Others",
    7:  "Pot Holes",
    8:  "Procession",
    9:  "Protest",
    10: "Public Event",
    11: "Road Conditions",
    12: "Test / Demo",
    13: "Tree Fall",
    14: "Vehicle Breakdown",
    15: "VIP Movement",
    16: "Water Logging",
    17: "Other (custom)",         # Added by us — saved to other_incidents.db
}

# veh_type: alphabetical order from LabelEncoder (NULL/empty → 'unknown' = 10)
VEHICLE_TYPE = {
    0:  "Auto Rickshaw",
    1:  "BMTC Bus",
    2:  "Heavy Vehicle",
    3:  "KSRTC Bus",
    4:  "LCV (Light Commercial Vehicle)",
    5:  "Others",
    6:  "Private Bus",
    7:  "Private Car",
    8:  "Taxi",
    9:  "Truck",
    10: "Unknown",
}

# corridor: alphabetical order from LabelEncoder on actual Data.csv
CORRIDOR = {
    0:  "Airport New South Road",
    1:  "Bannerghata Road",
    2:  "Bellary Road 1",
    3:  "Bellary Road 2",
    4:  "CBD 1",
    5:  "CBD 2",
    6:  "Hennur Main Road",
    7:  "Hosur Road",
    8:  "IRR (Thanisandra Road)",
    9:  "Magadi Road",
    10: "Mysore Road",
    11: "Non-Corridor",
    12: "ORR East 1",
    13: "ORR East 2",
    14: "ORR North 1",
    15: "ORR North 2",
    16: "ORR West 1",
    17: "Old Airport Road",
    18: "Old Madras Road",
    19: "Tumkur Road",
    20: "Varthur Road",
    21: "West of Chord Road",
    22: "Unknown",
}

# police_station: alphabetical order from LabelEncoder on actual Data.csv
POLICE_STATION = {
    0:  "Adugodi",
    1:  "Ashok Nagar",
    2:  "Banashankari",
    3:  "Banaswadi",
    4:  "Basavanagudi",
    5:  "Bellandur",
    6:  "Byatarayanapura",
    7:  "Chamarajpet",
    8:  "Chikkabanavara",
    9:  "Chikkajala",
    10: "City Market",
    11: "Cubbon Park",
    12: "Devanahalli Airport",
    13: "Electronic City",
    14: "HAL Old Airport",
    15: "HSR Layout",
    16: "Halasur",
    17: "Halasuru Gate",
    18: "Hebbala",
    19: "Hennuru",
    20: "High Ground",
    21: "Hulimavu",
    22: "J.P. Nagar",
    23: "Jalahalli",
    24: "Jayanagara",
    25: "Jeevanbheemanagar",
    26: "Jnanabharathi",
    27: "K.G. Halli",
    28: "K.R. Pura",
    29: "K.S. Layout",
    30: "Kamakshipalya",
    31: "Kengeri",
    32: "Kodigehalli",
    33: "Madiwala",
    34: "Magadi Road",
    35: "Mahadevapura",
    36: "Malleshwaram",
    37: "Mico Layout",
    38: "No Police Station",
    39: "Peenya",
    40: "Pulikeshinagar (F.Town)",
    41: "R.T. Nagar",
    42: "Rajajinagar",
    43: "Sadashivanagar",
    44: "Sheshadripuram",
    45: "Shivajinagar",
    46: "Thalagattapura",
    47: "Upparpet",
    48: "V.V. Puram (C.Pet)",
    49: "Vijayanagara",
    50: "Whitefield",
    51: "Wilson Garden",
    52: "Yelahanka",
    53: "Yeshwanthpura",
}

PRIORITY = {
    0: "LOW",
    1: "HIGH",
}

ROAD_CLOSURE = {
    0: "Not Required",
    1: "Required",
}

# day_of_week: alphabetical from LabelEncoder
DAY_OF_WEEK = {
    0: "Friday",
    1: "Monday",
    2: "Saturday",
    3: "Sunday",
    4: "Thursday",
    5: "Tuesday",
    6: "Wednesday",
}


def get_label(mapping: dict, code: int, default: str = "Unknown") -> str:
    """Get human-readable label for an encoded integer."""
    return mapping.get(code, default)
