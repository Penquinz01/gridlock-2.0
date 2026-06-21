"""
Similarity Service — KNN-based similar incident retrieval.

Uses sklearn's NearestNeighbors on the preprocessed dataset.
No vector DB, no embeddings, no LLMs.
"""

import numpy as np
from sklearn.neighbors import NearestNeighbors
from sklearn.preprocessing import StandardScaler
from app.ml import get_dataset
from app.config import SIMILARITY_FEATURES


# Module-level singletons — fitted once, reused
_knn = None
_scaler = None
_fitted = False


def _ensure_fitted():
    """Fit the KNN model on first use (lazy initialization)."""
    global _knn, _scaler, _fitted

    if _fitted:
        return

    df = get_dataset()
    X = df[SIMILARITY_FEATURES].values

    # Scale features so KNN distance is meaningful
    _scaler = StandardScaler()
    X_scaled = _scaler.fit_transform(X)

    _knn = NearestNeighbors(n_neighbors=20, metric="euclidean", algorithm="ball_tree")
    _knn.fit(X_scaled)

    _fitted = True


def find_similar(features: dict, top_k: int = 5) -> list[dict]:
    """
    Find similar incidents from the dataset.

    Args:
        features: dict with keys matching SIMILARITY_FEATURES
        top_k: number of similar incidents to return

    Returns:
        list of dicts, each representing a similar incident with distance
    """
    _ensure_fitted()

    df = get_dataset()

    # Build query vector
    query = np.array([[features[f] for f in SIMILARITY_FEATURES]])
    query_scaled = _scaler.transform(query)

    distances, indices = _knn.kneighbors(query_scaled, n_neighbors=min(top_k, len(df)))

    results = []
    for rank, (idx, dist) in enumerate(zip(indices[0], distances[0]), start=1):
        row = df.iloc[idx]
        results.append({
            "rank": rank,
            "distance": round(float(dist), 4),
            "event_type": int(row["event_type"]),
            "event_cause": int(row["event_cause"]),
            "veh_type": int(row["veh_type"]),
            "corridor": int(row["corridor"]),
            "priority": int(row["priority"]),
            "requires_road_closure": int(row["requires_road_closure"]),
            "police_station": int(row["police_station"]),
            "latitude": float(row["latitude"]),
            "longitude": float(row["longitude"]),
            "hour": int(row["hour"]),
            "day_of_week": int(row["day_of_week"]),
            "month": int(row["month"]),
        })

    return results
