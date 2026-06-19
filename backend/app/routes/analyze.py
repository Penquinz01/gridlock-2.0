"""
Analyze Route — POST /analyze

The main endpoint. Runs the full incident analysis pipeline:
    road closure → priority → risk → recommendation → similarity → diversion map
"""

from datetime import datetime
from fastapi import APIRouter
from app.schemas import IncidentInput, AnalyzeResponse
from app.services import priority_service, road_closure_service, risk_service
from app.services import recommendation_service, similarity_service, diversion_service
from app.database import save_incident

router = APIRouter(tags=["Analysis"])


def _generate_incident_id() -> str:
    """Generate a unique incident ID like INC-20260619-001."""
    now = datetime.now()
    timestamp = now.strftime("%Y%m%d-%H%M%S")
    return f"INC-{timestamp}"


@router.post("/analyze", response_model=AnalyzeResponse)
def analyze_incident(incident: IncidentInput):
    """
    Full incident analysis pipeline.

    Runs all services in sequence:
    1. Road Closure prediction (feeds into Priority)
    2. Priority prediction
    3. Risk assessment
    4. Resource recommendation
    5. Similar incident retrieval
    6. Diversion map generation
    """
    data = incident.model_dump()
    incident_id = _generate_incident_id()

    # Step 1: Road closure prediction (run first — priority model needs this)
    road_closure = road_closure_service.predict_road_closure(data)

    # Step 2: Priority prediction (uses road closure result as input)
    data_with_closure = {**data, "requires_road_closure": int(road_closure["required"])}
    priority = priority_service.predict_priority(data_with_closure)

    # Step 3: Risk assessment
    risk_input = {
        "priority": 1 if priority["label"] == "HIGH" else 0,
        "requires_road_closure": int(road_closure["required"]),
        "hour": data["hour"],
        "event_type": data["event_type"],
        "veh_type": data["veh_type"],
        "corridor": data["corridor"],
    }
    risk = risk_service.assess_risk(risk_input)

    # Step 4: Resource recommendation
    recommendation = recommendation_service.get_recommendation(
        risk_level=risk["level"],
        incident=risk_input,
    )

    # Step 5: Similar incidents
    similar = similarity_service.find_similar(data, top_k=5)

    # Step 6: Diversion map
    diversion_service.generate_diversion_map(
        latitude=data["latitude"],
        longitude=data["longitude"],
        incident_id=incident_id,
        corridor=data["corridor"],
        event_type=data["event_type"],
        priority_label=priority["label"],
        risk_level=risk["level"],
    )

    # Save to database
    save_incident({
        "id": incident_id,
        "created_at": datetime.now().isoformat(),
        **data,
        "priority": 1 if priority["label"] == "HIGH" else 0,
        "road_closure": int(road_closure["required"]),
        "risk_score": risk["score"],
        "risk_level": risk["level"],
        "officers": recommendation["officers"],
        "barricades": recommendation["barricades"],
        "escalation": recommendation["escalation"],
    })

    return AnalyzeResponse(
        incident_id=incident_id,
        priority=priority,
        road_closure=road_closure,
        risk=risk,
        recommendation=recommendation,
        similar_incidents=similar,
        diversion_map_url=f"/maps/{incident_id}.html",
    )
