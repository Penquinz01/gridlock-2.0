"""
ML Model Loader — Load trained models once at startup.
"""

import joblib
import pandas as pd
from app.config import PRIORITY_MODEL_PATH, ROAD_CLOSURE_MODEL_PATH, DATASET_PATH


# Module-level singletons — loaded once, used everywhere
_priority_model = None
_road_closure_model = None
_dataset = None


def load_models():
    """Load all ML models and dataset into memory. Call once at app startup."""
    global _priority_model, _road_closure_model, _dataset

    print("Loading priority model...")
    _priority_model = joblib.load(PRIORITY_MODEL_PATH)

    print("Loading road closure model...")
    _road_closure_model = joblib.load(ROAD_CLOSURE_MODEL_PATH)

    print("Loading dataset...")
    _dataset = pd.read_csv(DATASET_PATH)

    print(f"Models loaded. Dataset: {len(_dataset)} rows.")


def get_priority_model():
    """Get the priority prediction model."""
    if _priority_model is None:
        raise RuntimeError("Models not loaded. Call load_models() first.")
    return _priority_model


def get_road_closure_model():
    """Get the road closure prediction model."""
    if _road_closure_model is None:
        raise RuntimeError("Models not loaded. Call load_models() first.")
    return _road_closure_model


def get_dataset() -> pd.DataFrame:
    """Get the preprocessed dataset."""
    if _dataset is None:
        raise RuntimeError("Dataset not loaded. Call load_models() first.")
    return _dataset


def models_loaded() -> bool:
    """Check if all models are loaded."""
    return all([_priority_model is not None, _road_closure_model is not None, _dataset is not None])
