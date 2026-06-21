"""
Station Portal Route — Handlers for police station authentication, queues, and feedback loops.
"""

from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, Query, Header
from typing import Optional

from app.schemas import (
    LoginRequest, LoginResponse, FeedbackInput, FeedbackResponse
)
from app.database import (
    get_incidents_by_station, get_incident_by_id, save_feedback_and_resolve,
    get_feedback_for_incident, get_other_incident
)
from app.services.auth_service import authenticate_station, verify_token

router = APIRouter(prefix="/api/portal", tags=["Station Portal"])


from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

security_scheme = HTTPBearer(auto_error=False)

def get_current_station_id(credentials: Optional[HTTPAuthorizationCredentials] = Depends(security_scheme)) -> int:
    """Dependency to extract and verify the station ID from the Authorization header."""
    if not credentials:
        raise HTTPException(status_code=401, detail="Authorization header missing or invalid")

    token = credentials.credentials
    return verify_token(token)



@router.post("/login", response_model=LoginResponse)
def login(request: LoginRequest):
    """
    Authenticate a police station using station_id and password.
    For station X, use password: 'station_pass_X'.
    """
    token = authenticate_station(request.police_station, request.password)
    return LoginResponse(
        success=True,
        token=token,
        station_id=request.police_station,
        station_name=f"Police Station #{request.police_station}"
    )


@router.get("/incidents/{station_id}")
def get_station_incidents(
    station_id: int,
    status: Optional[str] = Query(None, description="Filter by status: 'ACTIVE' or 'RESOLVED'"),
    current_station: int = Depends(get_current_station_id)
):
    """
    Fetch all incidents assigned to the specified police station.
    Secured: Station can only fetch its own incidents.
    """
    if current_station != station_id:
        raise HTTPException(
            status_code=403,
            detail="Forbidden: You cannot access another police station's queue"
        )

    incidents = get_incidents_by_station(station_id, status)
    
    # Attach descriptions for incidents with cause 'Other' (17) from the secondary database
    for inc in incidents:
        if inc["event_cause"] == 17:
            other_rec = get_other_incident(inc["id"])
            inc["description"] = other_rec["description"] if other_rec else None

    return {
        "station_id": station_id,
        "count": len(incidents),
        "incidents": incidents
    }


@router.post("/incidents/{incident_id}/feedback", response_model=FeedbackResponse)
def submit_incident_feedback(
    incident_id: str,
    feedback: FeedbackInput,
    current_station: int = Depends(get_current_station_id)
):
    """
    Submit post-incident retrospective feedback (post-learning ground truth)
    and mark the incident as RESOLVED.
    """
    incident = get_incident_by_id(incident_id)
    if not incident:
        raise HTTPException(status_code=404, detail="Incident not found")

    # Check that this incident is actually assigned to the logged-in station
    if incident["police_station"] != current_station:
        raise HTTPException(
            status_code=403,
            detail="Forbidden: You can only resolve incidents assigned to your station"
        )

    # Save learning data and resolve
    feedback_data = {
        "incident_id": incident_id,
        "submitted_at": datetime.now().isoformat(),
        "actual_officers": feedback.actual_officers,
        "actual_barricades": feedback.actual_barricades,
        "actual_road_closure": feedback.actual_road_closure,
        "actual_priority": feedback.actual_priority,
        "feedback_notes": feedback.feedback_notes,
    }
    save_feedback_and_resolve(feedback_data)

    return FeedbackResponse(
        success=True,
        incident_id=incident_id
    )


@router.get("/incidents/{incident_id}/feedback")
def view_incident_feedback(
    incident_id: str,
    current_station: int = Depends(get_current_station_id)
):
    """
    Retrieve feedback details for a resolved incident.
    """
    incident = get_incident_by_id(incident_id)
    if not incident:
        raise HTTPException(status_code=404, detail="Incident not found")

    if incident["police_station"] != current_station:
        raise HTTPException(
            status_code=403,
            detail="Forbidden: You can only view feedback for your station"
        )

    feedback = get_feedback_for_incident(incident_id)
    if not feedback:
        raise HTTPException(status_code=404, detail="Feedback not found for this incident")

    return feedback
