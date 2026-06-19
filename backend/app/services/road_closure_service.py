"""
Road Closure Service — Predicts whether road closure is needed.
"""

import pandas as pd
from app.ml import get_road_closure_model
from app.config import ROAD_CLOSURE_MODEL_FEATURES


def predict_road_closure(features: dict) -> dict:
    """
    Predict whether road closure is required.

    Args:
        features: dict with keys matching ROAD_CLOSURE_MODEL_FEATURES

    Returns:
        {"required": bool, "confidence": float}
    """
    model = get_road_closure_model()

    X = pd.DataFrame([{f: features[f] for f in ROAD_CLOSURE_MODEL_FEATURES}])

    prediction = model.predict(X)[0]
    probabilities = model.predict_proba(X)[0]
    confidence = float(probabilities[prediction])

    return {
        "required": bool(prediction == 1),
        "confidence": round(confidence, 3),
    }
