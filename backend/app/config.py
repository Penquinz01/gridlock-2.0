"""
ARES Configuration — All paths and constants in one place.
"""

import os
from pathlib import Path

# Base directory is the backend/ folder
BASE_DIR = Path(__file__).resolve().parent.parent

# Load .env manually if it exists in backend/ or root workspace directory
def _load_dotenv():
    for p in [BASE_DIR / ".env", BASE_DIR.parent / ".env"]:
        if p.is_file():
            with open(p, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith("#") and "=" in line:
                        parts = line.split("=", 1)
                        key = parts[0].strip()
                        val = parts[1].strip().strip('"').strip("'")
                        if key:
                            os.environ.setdefault(key, val)

_load_dotenv()

# MapmyIndia / Mappls API (optional — for nearby police station lookup)
MAPMYINDIA_API_KEY = os.environ.get("MAPMYINDIA_API_KEY", "")
MAPMYINDIA_CLIENT_ID = os.environ.get("MAPMYINDIA_CLIENT_ID", "")
MAPMYINDIA_CLIENT_SECRET = os.environ.get("MAPMYINDIA_CLIENT_SECRET", "")



# Model paths
PRIORITY_MODEL_PATH = BASE_DIR / "models" / "priority_model.pkl"
ROAD_CLOSURE_MODEL_PATH = BASE_DIR / "models" / "road_closure_model.pkl"

# Dataset
DATASET_PATH = BASE_DIR / "preprocessed_data" / "preprocessed_data.csv"

# Database
DB_PATH = BASE_DIR / "ares.db"
OTHER_DB_PATH = BASE_DIR / "other_incidents.db"

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
