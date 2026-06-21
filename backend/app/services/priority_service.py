"""
Priority Service — Predicts incident priority using the trained model.
"""

import pandas as pd
from app.ml import get_priority_model
from app.config import PRIORITY_MODEL_FEATURES


def predict_priority(features: dict) -> dict:
    """
    Predict incident priority.

    Args:
        features: dict with keys matching PRIORITY_MODEL_FEATURES

    Returns:
        {"label": "HIGH" or "LOW", "confidence": float}
    """
    model = get_priority_model()

    # Build DataFrame with correct column names (avoids sklearn warnings)
    X = pd.DataFrame([{f: features[f] for f in PRIORITY_MODEL_FEATURES}])

    prediction = model.predict(X)[0]
    probabilities = model.predict_proba(X)[0]
    confidence = float(probabilities[prediction])

    return {
        "label": "HIGH" if prediction == 1 else "LOW",
        "confidence": round(confidence, 3),
    }
