"""
API-level tests — test all endpoints return expected status codes.
"""

import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_root():
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert "endpoints" in data


def test_health():
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] in ("healthy", "degraded")
    assert data["models_loaded"] is True
    assert data["dataset_rows"] > 0


def test_hotspots_no_filter():
    response = client.get("/hotspots")
    assert response.status_code == 200
    data = response.json()
    assert data["total_incidents"] > 0
    assert len(data["hotspots"]) > 0


def test_hotspots_with_filter():
    response = client.get("/hotspots?hour=17&day_of_week=4")
    assert response.status_code == 200
    data = response.json()
    assert data["filters_applied"]["hour"] == 17
    assert data["filters_applied"]["day_of_week"] == 4


def test_recommendation():
    response = client.post("/recommendation", json={
        "risk_level": "HIGH",
        "event_type": 1,
        "requires_road_closure": 1,
        "priority": 1,
    })
    assert response.status_code == 200
    data = response.json()
    assert data["officers"] > 0
    assert data["escalation"] == "ACP"


def test_diversion():
    response = client.post("/diversion", json={
        "latitude": 13.04,
        "longitude": 77.518,
    })
    assert response.status_code == 200
    data = response.json()
    assert "<div" in data["map_html"] or "<iframe" in data["map_html"] or "folium" in data["map_html"].lower()
    assert data["incident_location"]["latitude"] == 13.04
