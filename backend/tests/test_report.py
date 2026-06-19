"""
Tests for the simplified /report endpoint and supporting logic.
"""

import pytest
from datetime import datetime
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


# ─── Time parsing ───────────────────────────────────────────────

class TestTimeParsing:
    """Test time string parsing logic."""

    def test_valid_iso_format(self):
        """Valid ISO time string should be accepted."""
        resp = client.post("/report", json={
            "latitude": 13.04,
            "longitude": 77.518,
            "event_cause": 14,
            "time": "2026-06-19T15:30:00",
        })
        assert resp.status_code == 200
        data = resp.json()
        assert data["inferred"]["hour"] == 15
        assert data["inferred"]["day_of_week"] == 4  # Friday
        assert data["inferred"]["month"] == 6

    def test_invalid_time_format(self):
        """Invalid time format should return 400."""
        resp = client.post("/report", json={
            "latitude": 13.04,
            "longitude": 77.518,
            "event_cause": 14,
            "time": "not-a-date",
        })
        assert resp.status_code == 400

    def test_time_with_date_only(self):
        """Date-only ISO string (no time) should default hour to 0."""
        resp = client.post("/report", json={
            "latitude": 13.04,
            "longitude": 77.518,
            "event_cause": 14,
            "time": "2026-06-19",
        })
        assert resp.status_code == 200
        assert resp.json()["inferred"]["hour"] == 0


# ─── Event type inference ───────────────────────────────────────

class TestEventTypeInference:
    """Test event_type is correctly inferred from event_cause."""

    def test_minor_cause_maps_to_minor(self):
        """Rash Driving (cause=0) → Minor (type=0)."""
        resp = client.post("/report", json={
            "latitude": 13.04,
            "longitude": 77.518,
            "event_cause": 0,
            "time": "2026-06-19T12:00:00",
        })
        assert resp.status_code == 200
        assert resp.json()["inferred"]["event_type"] == 0
        assert resp.json()["inferred"]["event_type_label"] == "Minor Incident"

    def test_major_cause_maps_to_major(self):
        """Head On Collision (cause=15) → Major (type=1)."""
        resp = client.post("/report", json={
            "latitude": 13.04,
            "longitude": 77.518,
            "event_cause": 15,
            "time": "2026-06-19T12:00:00",
        })
        assert resp.status_code == 200
        assert resp.json()["inferred"]["event_type"] == 1
        assert resp.json()["inferred"]["event_type_label"] == "Major Incident"


# ─── Location resolution ───────────────────────────────────────

class TestLocationResolution:
    """Test that location is resolved from coordinates."""

    def test_corridor_is_resolved(self):
        """Corridor should be inferred from the nearest dataset record."""
        resp = client.post("/report", json={
            "latitude": 13.04,
            "longitude": 77.518,
            "event_cause": 14,
            "time": "2026-06-19T15:30:00",
        })
        assert resp.status_code == 200
        loc = resp.json()["location"]
        assert "corridor" in loc
        assert "corridor_name" in loc
        assert isinstance(loc["corridor"], int)

    def test_police_station_is_resolved(self):
        """Police station should be resolved from dataset."""
        resp = client.post("/report", json={
            "latitude": 12.92,
            "longitude": 77.64,
            "event_cause": 2,
            "time": "2026-06-19T08:00:00",
        })
        assert resp.status_code == 200
        loc = resp.json()["location"]
        assert "police_station" in loc
        assert isinstance(loc["police_station"], int)


# ─── Full pipeline ──────────────────────────────────────────────

class TestFullPipeline:
    """Test the complete /report response structure."""

    def test_response_has_all_fields(self):
        """Response should contain all expected top-level fields."""
        resp = client.post("/report", json={
            "latitude": 13.04,
            "longitude": 77.518,
            "event_cause": 14,
            "time": "2026-06-19T17:30:00",
        })
        assert resp.status_code == 200
        data = resp.json()

        # Top-level keys
        assert "incident_id" in data
        assert data["incident_id"].startswith("INC-")
        assert "location" in data
        assert "inferred" in data
        assert "priority" in data
        assert "road_closure" in data
        assert "risk" in data
        assert "recommendation" in data
        assert "similar_incidents" in data
        assert "diversion_map_url" in data

    def test_priority_has_label_and_confidence(self):
        """Priority result should have label and confidence."""
        resp = client.post("/report", json={
            "latitude": 13.04,
            "longitude": 77.518,
            "event_cause": 14,
            "time": "2026-06-19T17:30:00",
        })
        data = resp.json()
        assert data["priority"]["label"] in ("HIGH", "LOW")
        assert 0 <= data["priority"]["confidence"] <= 1

    def test_road_closure_has_required_and_confidence(self):
        """Road closure result should have required flag and confidence."""
        resp = client.post("/report", json={
            "latitude": 13.04,
            "longitude": 77.518,
            "event_cause": 14,
            "time": "2026-06-19T17:30:00",
        })
        data = resp.json()
        assert isinstance(data["road_closure"]["required"], bool)
        assert 0 <= data["road_closure"]["confidence"] <= 1

    def test_default_veh_type_is_car(self):
        """veh_type should default to 2 (Car/Sedan)."""
        resp = client.post("/report", json={
            "latitude": 13.04,
            "longitude": 77.518,
            "event_cause": 14,
            "time": "2026-06-19T17:30:00",
        })
        data = resp.json()
        assert data["inferred"]["veh_type"] == 2
        assert data["inferred"]["veh_type_label"] == "Car/Sedan"


# ─── Validation ─────────────────────────────────────────────────

class TestValidation:
    """Test input validation."""

    def test_missing_required_field(self):
        """Missing time field should return 422."""
        resp = client.post("/report", json={
            "latitude": 13.04,
            "longitude": 77.518,
            "event_cause": 14,
        })
        assert resp.status_code == 422

    def test_latitude_out_of_range(self):
        """Latitude outside Bengaluru range should return 422."""
        resp = client.post("/report", json={
            "latitude": 28.0,  # Delhi, not Bengaluru
            "longitude": 77.518,
            "event_cause": 14,
            "time": "2026-06-19T15:30:00",
        })
        assert resp.status_code == 422
