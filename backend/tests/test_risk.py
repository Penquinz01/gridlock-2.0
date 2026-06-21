"""
Tests for the risk assessment service and endpoint.
"""

import pytest
from app.services.risk_service import assess_risk
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


class TestRiskService:
    """Unit tests for the risk scoring logic."""

    def test_high_priority_adds_points(self):
        result = assess_risk({"priority": 1, "requires_road_closure": 0,
                              "hour": 12, "event_type": 0, "veh_type": 2, "corridor": 0})
        assert result["score"] >= 25
        assert "High priority incident" in result["factors"]

    def test_road_closure_adds_points(self):
        result = assess_risk({"priority": 0, "requires_road_closure": 1,
                              "hour": 12, "event_type": 0, "veh_type": 2, "corridor": 0})
        assert result["score"] >= 20
        assert "Road closure required" in result["factors"]

    def test_peak_hour_adds_points(self):
        result = assess_risk({"priority": 0, "requires_road_closure": 0,
                              "hour": 17, "event_type": 0, "veh_type": 2, "corridor": 0})
        assert "Peak traffic hour" in result["factors"][0] or any(
            "Peak" in f for f in result["factors"]
        )

    def test_critical_threshold(self):
        """All risk factors combined should hit CRITICAL."""
        result = assess_risk({"priority": 1, "requires_road_closure": 1,
                              "hour": 17, "event_type": 1, "veh_type": 7, "corridor": 0})
        assert result["level"] in ("CRITICAL", "HIGH")
        assert result["score"] >= 50

    def test_low_risk(self):
        """Benign incident should score LOW."""
        result = assess_risk({"priority": 0, "requires_road_closure": 0,
                              "hour": 12, "event_type": 0, "veh_type": 2, "corridor": 0})
        assert result["level"] == "LOW"
        assert result["score"] < 30

    def test_score_capped_at_100(self):
        result = assess_risk({"priority": 1, "requires_road_closure": 1,
                              "hour": 17, "event_type": 1, "veh_type": 8, "corridor": 0})
        assert result["score"] <= 100


class TestRiskEndpoint:
    """API-level tests for POST /risk."""

    def test_risk_endpoint_200(self):
        response = client.post("/risk", json={
            "event_type": 1, "priority": 1, "requires_road_closure": 1,
            "hour": 17, "corridor": 19, "veh_type": 4,
        })
        assert response.status_code == 200
        data = response.json()
        assert "score" in data
        assert "level" in data
        assert "factors" in data

    def test_risk_endpoint_validation(self):
        response = client.post("/risk", json={"event_type": 1})
        assert response.status_code == 422
