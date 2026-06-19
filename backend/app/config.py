"""
ARES Configuration — All paths and constants in one place.
"""

import os
from pathlib import Path

# MapmyIndia / Mappls API (optional — for nearby police station lookup)
MAPMYINDIA_CLIENT_ID = os.environ.get("MAPMYINDIA_CLIENT_ID", "")
MAPMYINDIA_CLIENT_SECRET = os.environ.get("MAPMYINDIA_CLIENT_SECRET", "")

# Base directory is the backend/ folder
BASE_DIR = Path(__file__).resolve().parent.parent

# Model paths
PRIORITY_MODEL_PATH = BASE_DIR / "models" / "priority_model.pkl"
ROAD_CLOSURE_MODEL_PATH = BASE_DIR / "models" / "road_closure_model.pkl"

# Dataset
DATASET_PATH = BASE_DIR / "preprocessed_data" / "preprocessed_data.csv"

# Database
DB_PATH = BASE_DIR / "ares.db"

# Generated maps directory
MAPS_DIR = BASE_DIR / "generated_maps"
MAPS_DIR.mkdir(exist_ok=True)

# API settings
API_TITLE = "ARES — AI-Powered Incident Response Copilot"
API_VERSION = "1.0.0"
API_DESCRIPTION = "Backend API for Bengaluru Traffic Police incident response system"

# KNN settings
DEFAULT_TOP_K = 5
MAX_TOP_K = 20

# Feature lists (must match what the models were trained on)
PRIORITY_MODEL_FEATURES = [
    "event_type", "event_cause", "requires_road_closure",
    "veh_type", "hour", "day_of_week", "month"
]

ROAD_CLOSURE_MODEL_FEATURES = [
    "event_type", "event_cause", "veh_type",
    "hour", "day_of_week", "month"
]

SIMILARITY_FEATURES = [
    "event_type", "event_cause", "veh_type",
    "corridor", "hour", "day_of_week", "month"
]
