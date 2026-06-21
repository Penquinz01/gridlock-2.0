"""
Hotspot Service — Identifies incident hotspots from the dataset.

Groups incidents by location (rounded lat/lon) and corridor,
then ranks by incident count and high-priority percentage.
"""

import numpy as np
from app.ml import get_dataset


def get_hotspots(
    hour: int = None,
    day_of_week: int = None,
    month: int = None,
    event_type: int = None,
    top_n: int = 20,
) -> dict:
    """
    Get incident hotspots with optional filters.

    Returns:
        {"total_incidents": int, "hotspots": list[dict], "filters_applied": dict}
    """
    df = get_dataset().copy()

    # Apply filters
    filters_applied = {}
    if hour is not None:
        df = df[df["hour"] == hour]
        filters_applied["hour"] = hour
    if day_of_week is not None:
        df = df[df["day_of_week"] == day_of_week]
        filters_applied["day_of_week"] = day_of_week
    if month is not None:
        df = df[df["month"] == month]
        filters_applied["month"] = month
    if event_type is not None:
        df = df[df["event_type"] == event_type]
        filters_applied["event_type"] = event_type

    if len(df) == 0:
        return {"total_incidents": 0, "hotspots": [], "filters_applied": filters_applied}

    # Round lat/lon to ~100m grid for clustering
    df["lat_round"] = np.round(df["latitude"], 3)
    df["lon_round"] = np.round(df["longitude"], 3)

    # Group by rounded location + corridor
    grouped = df.groupby(["lat_round", "lon_round", "corridor"]).agg(
        incident_count=("event_type", "count"),
        high_priority_count=("priority", "sum"),
        avg_lat=("latitude", "mean"),
        avg_lon=("longitude", "mean"),
    ).reset_index()

    grouped["high_priority_pct"] = round(
        grouped["high_priority_count"] / grouped["incident_count"], 3
    )

    # Sort by incident count descending
    grouped = grouped.sort_values("incident_count", ascending=False).head(top_n)

    hotspots = []
    for _, row in grouped.iterrows():
        hotspots.append({
            "latitude": round(float(row["avg_lat"]), 6),
            "longitude": round(float(row["avg_lon"]), 6),
            "corridor": int(row["corridor"]),
            "incident_count": int(row["incident_count"]),
            "high_priority_pct": float(row["high_priority_pct"]),
        })

    return {
        "total_incidents": len(df),
        "hotspots": hotspots,
        "filters_applied": filters_applied,
    }
