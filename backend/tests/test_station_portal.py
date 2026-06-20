"""
Tests for the Police Station Portal endpoints and the post-incident learning loop.
"""

import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.database import get_incident_by_id, get_feedback_for_incident

client = TestClient(app)


# --- Helper to create a report ---
def create_sample_incident() -> str:
    """Helper to report an incident and return the generated incident_id."""
    resp = client.post("/report", json={
        "latitude": 13.04,
        "longitude": 77.518,
        "event_cause": 14,
        "time": "2026-06-19T15:30:00"
    })
    assert resp.status_code == 200
    return resp.json()["incident_id"], resp.json()["location"]["police_station"]


# ─── Authentication Tests ───────────────────────────────────────

class TestStationPortalAuth:
    """Test police station portal login and authorization controls."""

    def test_login_success(self):
        """Should succeed with correct password 'station_pass_<station_id>'."""
        resp = client.post("/api/portal/login", json={
            "police_station": 39,
            "password": "station_pass_39"
        })
        assert resp.status_code == 200
        data = resp.json()
        assert data["success"] is True
        assert "token" in data
        assert data["station_id"] == 39

    def test_login_invalid_password(self):
        """Should return 401 Unauthorized for incorrect password."""
        resp = client.post("/api/portal/login", json={
            "police_station": 39,
            "password": "wrong_password"
        })
        assert resp.status_code == 401


# ─── Queue Retrieval Tests ──────────────────────────────────────

class TestStationQueue:
    """Test retrieving incidents assigned to a police station."""

    def test_get_station_incidents_success(self):
        """Logged-in station should successfully get its queue."""
        # 1. Login
        login_resp = client.post("/api/portal/login", json={
            "police_station": 39,
            "password": "station_pass_39"
        })
        token = login_resp.json()["token"]

        # 2. Get incidents
        resp = client.get(
            "/api/portal/incidents/39",
            headers={"Authorization": f"Bearer {token}"}
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["station_id"] == 39
        assert "incidents" in data

    def test_get_station_incidents_forbidden(self):
        """Logged-in station 39 should be forbidden from accessing station 40's queue."""
        # 1. Login as station 39
        login_resp = client.post("/api/portal/login", json={
            "police_station": 39,
            "password": "station_pass_39"
        })
        token = login_resp.json()["token"]

        # 2. Try to fetch station 40
        resp = client.get(
            "/api/portal/incidents/40",
            headers={"Authorization": f"Bearer {token}"}
        )
        assert resp.status_code == 403

    def test_get_station_incidents_unauthorized(self):
        """Accessing a queue without a token should return 401."""
        resp = client.get("/api/portal/incidents/39")
        assert resp.status_code == 401

    def test_get_station_incidents_with_custom_description(self):
        """Queue should include the custom description for cause 17 from the secondary DB."""
        custom_desc = "Water pipe burst, completely flooding the road."
        # 1. Report incident with cause 17
        report_resp = client.post("/report", json={
            "latitude": 13.04,
            "longitude": 77.518,
            "event_cause": 17,  # Other
            "time": "2026-06-19T15:30:00",
            "description": custom_desc
        })
        incident_id = report_resp.json()["incident_id"]
        station_id = report_resp.json()["location"]["police_station"]

        # 2. Login
        login_resp = client.post("/api/portal/login", json={
            "police_station": station_id,
            "password": f"station_pass_{station_id}"
        })
        token = login_resp.json()["token"]

        # 3. Get queue
        resp = client.get(
            f"/api/portal/incidents/{station_id}",
            headers={"Authorization": f"Bearer {token}"}
        )
        assert resp.status_code == 200
        incidents = resp.json()["incidents"]
        
        # 4. Verify description is attached
        target = next(i for i in incidents if i["id"] == incident_id)
        assert target["event_cause"] == 17
        assert target["description"] == custom_desc



# ─── Feedback & Resolution Learning Loop ────────────────────────

class TestFeedbackLoop:
    """Test the post-incident retrospective feedback cycle."""

    def test_submit_feedback_lifecycle(self):
        """Test submitting feedback, database update, status resolving, and feedback retrieval."""
        # 1. Create an incident and get its ID and resolved station
        incident_id, station_id = create_sample_incident()

        # 2. Log in as that resolved station
        login_resp = client.post("/api/portal/login", json={
            "police_station": station_id,
            "password": f"station_pass_{station_id}"
        })
        token = login_resp.json()["token"]

        # 3. Verify it appears in the active queue
        queue_resp = client.get(
            f"/api/portal/incidents/{station_id}?status=ACTIVE",
            headers={"Authorization": f"Bearer {token}"}
        )
        active_ids = [inc["id"] for inc in queue_resp.json()["incidents"]]
        assert incident_id in active_ids

        # 4. Submit feedback (post-learning ground truth)
        feedback_input = {
            "actual_officers": 5,
            "actual_barricades": 8,
            "actual_road_closure": 1,
            "actual_priority": 1,
            "feedback_notes": "Heavy rains made a road closure absolutely necessary. Deployed 5 officers."
        }
        feedback_resp = client.post(
            f"/api/portal/incidents/{incident_id}/feedback",
            json=feedback_input,
            headers={"Authorization": f"Bearer {token}"}
        )
        assert feedback_resp.status_code == 200
        assert feedback_resp.json()["success"] is True

        # 5. Verify the status is now 'RESOLVED' in the DB
        incident_db = get_incident_by_id(incident_id)
        assert incident_db["status"] == "RESOLVED"

        # 6. Verify it is no longer in the ACTIVE queue, but is in the RESOLVED queue
        active_queue = client.get(
            f"/api/portal/incidents/{station_id}?status=ACTIVE",
            headers={"Authorization": f"Bearer {token}"}
        ).json()
        assert incident_id not in [inc["id"] for inc in active_queue["incidents"]]

        resolved_queue = client.get(
            f"/api/portal/incidents/{station_id}?status=RESOLVED",
            headers={"Authorization": f"Bearer {token}"}
        ).json()
        assert incident_id in [inc["id"] for inc in resolved_queue["incidents"]]

        # 7. Retrieve the feedback and verify the details
        get_feedback_resp = client.get(
            f"/api/portal/incidents/{incident_id}/feedback",
            headers={"Authorization": f"Bearer {token}"}
        )
        assert get_feedback_resp.status_code == 200
        feedback_data = get_feedback_resp.json()
        assert feedback_data["actual_officers"] == 5
        assert feedback_data["actual_barricades"] == 8
        assert feedback_data["actual_road_closure"] == 1
        assert feedback_data["actual_priority"] == 1
        assert feedback_data["feedback_notes"] == feedback_input["feedback_notes"]

    def test_submit_feedback_unauthorized_station(self):
        """Station X should be forbidden from submitting feedback for station Y's incident."""
        # 1. Create incident assigned to station X
        incident_id, station_id = create_sample_incident()
        other_station = (station_id + 1) % 54

        # 2. Login as station Y
        login_resp = client.post("/api/portal/login", json={
            "police_station": other_station,
            "password": f"station_pass_{other_station}"
        })
        token = login_resp.json()["token"]

        # 3. Try to submit feedback for station X's incident
        resp = client.post(
            f"/api/portal/incidents/{incident_id}/feedback",
            json={
                "actual_officers": 2,
                "actual_barricades": 4,
                "actual_road_closure": 0,
                "actual_priority": 0
            },
            headers={"Authorization": f"Bearer {token}"}
        )
        assert resp.status_code == 403
