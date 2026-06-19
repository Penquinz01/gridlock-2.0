"""
Tests for the similarity service and endpoint.
"""

import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

SAMPLE_QUERY = {
    "event_type": 1,
    "event_cause": 14,
    "veh_type": 4,
    "corridor": 19,
    "hour": 17,
    "day_of_week": 4,
    "month": 3,
    "top_k": 5,
}


def test_similar_incidents_returns_results():
    response = client.post("/similar-incidents", json=SAMPLE_QUERY)
    assert response.status_code == 200

    data = response.json()
    assert data["count"] == 5
    assert len(data["similar_incidents"]) == 5

    # Results should be ranked
    assert data["similar_incidents"][0]["rank"] == 1

    # Distances should be non-negative and sorted
    distances = [s["distance"] for s in data["similar_incidents"]]
    assert all(d >= 0 for d in distances)
    assert distances == sorted(distances)


def test_similar_incidents_custom_top_k():
    query = {**SAMPLE_QUERY, "top_k": 3}
    response = client.post("/similar-incidents", json=query)
    assert response.status_code == 200
    assert response.json()["count"] == 3


def test_similar_incidents_validation():
    response = client.post("/similar-incidents", json={"event_type": 1})
    assert response.status_code == 422
