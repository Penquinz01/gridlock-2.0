"""
Tests for the /analyze endpoint — the core pipeline.
"""

import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

SAMPLE_INCIDENT = {
    "event_type": 1,
    "event_cause": 14,
    "veh_type": 4,
    "corridor": 19,
    "police_station": 39,
    "latitude": 13.04,
    "longitude": 77.518,
    "hour": 17,
    "day_of_week": 4,
    "month": 3,
}


def test_analyze_returns_200():
    """Full pipeline should return 200 with all fields populated."""
    response = client.post("/analyze", json=SAMPLE_INCIDENT)
    assert response.status_code == 200

    data = response.json()
    assert "incident_id" in data
    assert data["incident_id"].startswith("INC-")

    # Priority
    assert data["priority"]["label"] in ("HIGH", "LOW")
    assert 0 <= data["priority"]["confidence"] <= 1

    # Road closure
    assert isinstance(data["road_closure"]["required"], bool)
    assert 0 <= data["road_closure"]["confidence"] <= 1

    # Risk
    assert 0 <= data["risk"]["score"] <= 100
    assert data["risk"]["level"] in ("CRITICAL", "HIGH", "MEDIUM", "LOW")
    assert isinstance(data["risk"]["factors"], list)

    # Recommendation
    assert data["recommendation"]["officers"] > 0
    assert data["recommendation"]["escalation"] in ("DCP", "ACP", "Inspector", "Sub-Inspector")

    # Similar incidents
    assert len(data["similar_incidents"]) > 0
    assert data["similar_incidents"][0]["rank"] == 1

    # Diversion map URL
    assert data["diversion_map_url"].startswith("/maps/")


def test_analyze_validation_error():
    """Missing required fields should return 422."""
    response = client.post("/analyze", json={"event_type": 1})
    assert response.status_code == 422


def test_analyze_out_of_range():
    """Out-of-range values should return 422."""
    bad = {**SAMPLE_INCIDENT, "hour": 25}
    response = client.post("/analyze", json=bad)
    assert response.status_code == 422
