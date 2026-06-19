"""
Report Route — POST /report

Simplified endpoint for frontend.
Accepts only: latitude, longitude, event_cause, time.
Auto-infers everything else and runs the full analysis pipeline.
"""

from datetime import datetime
from fastapi import APIRouter, HTTPException

from app.schemas import (
    SimplifiedIncidentInput, SimplifiedAnalyzeResponse,
    LocationInfo, InferredFields,
)
from app.services import (
    priority_service, road_closure_service, risk_service,
    recommendation_service, similarity_service, diversion_service,
)
from app.services.location_service import resolve_full_location
from app.database import save_incident
from app.utils.mappings import EVENT_TYPE, EVENT_CAUSE, VEHICLE_TYPE, CORRIDOR, get_label

router = APIRouter(tags=["Report"])


# ─── Inference helpers ──────────────────────────────────────────

# Causes that usually involve serious / major incidents
_MAJOR_CAUSES = {4, 5, 8, 11, 12, 15}  # Drunk, Distracted, Weather, Tyre Burst, Brake Fail, Head-On

DEFAULT_VEH_TYPE = 2  # Car/Sedan — safest default when unknown


def _infer_event_type(event_cause: int) -> int:
    """Infer event_type from event_cause. Major causes → 1, else → 0."""
    return 1 if event_cause in _MAJOR_CAUSES else 0


def _parse_time(time_str: str) -> dict:
    """Parse ISO datetime string into hour, day_of_week, month."""
    try:
        dt = datetime.fromisoformat(time_str)
    except ValueError:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid time format: '{time_str}'. Use ISO 8601, e.g. 2026-06-19T15:30:00",
        )
    return {
        "hour": dt.hour,
        "day_of_week": dt.weekday(),  # 0=Monday, 6=Sunday
        "month": dt.month,
    }


def _generate_incident_id() -> str:
    """Generate a unique incident ID like INC-20260619-153000."""
    return f"INC-{datetime.now().strftime('%Y%m%d-%H%M%S')}"


# ─── Endpoint ───────────────────────────────────────────────────

@router.post("/report", response_model=SimplifiedAnalyzeResponse)
def report_incident(input: SimplifiedIncidentInput):
    """
    Simplified incident report endpoint.

    Frontend sends only: latitude, longitude, event_cause, time.
    Backend auto-infers all remaining fields and runs the full pipeline:
      1. Resolve location → corridor + police_station
      2. Parse time → hour, day_of_week, month
      3. Infer event_type from cause
      4. Road Closure prediction
      5. Priority prediction
      6. Risk assessment
      7. Resource recommendation
      8. Similar incident retrieval
      9. Diversion map generation
    """
    incident_id = _generate_incident_id()

    # --- Step 1: Resolve location ---
    location = resolve_full_location(input.latitude, input.longitude)

    # --- Step 2: Parse time ---
    time_parts = _parse_time(input.time)

    # --- Step 3: Infer missing features ---
    event_type = _infer_event_type(input.event_cause)
    veh_type = DEFAULT_VEH_TYPE

    # Build the full feature dict (same shape the models expect)
    data = {
        "event_type": event_type,
        "event_cause": input.event_cause,
        "veh_type": veh_type,
        "corridor": location["corridor"],
        "police_station": location["police_station"],
        "latitude": input.latitude,
        "longitude": input.longitude,
        **time_parts,
    }

    # --- Step 4: Road closure prediction (must run first) ---
    road_closure = road_closure_service.predict_road_closure(data)

    # --- Step 5: Priority prediction (needs road closure result) ---
    data_with_closure = {**data, "requires_road_closure": int(road_closure["required"])}
    priority = priority_service.predict_priority(data_with_closure)

    # --- Step 6: Risk assessment ---
    risk_input = {
        "priority": 1 if priority["label"] == "HIGH" else 0,
        "requires_road_closure": int(road_closure["required"]),
        "hour": data["hour"],
        "event_type": data["event_type"],
        "veh_type": data["veh_type"],
        "corridor": data["corridor"],
    }
    risk = risk_service.assess_risk(risk_input)

    # --- Step 7: Resource recommendation ---
    recommendation = recommendation_service.get_recommendation(
        risk_level=risk["level"],
        incident=risk_input,
    )

    # --- Step 8: Similar incidents ---
    similar = similarity_service.find_similar(data, top_k=5)

    # --- Step 9: Diversion map ---
    diversion_service.generate_diversion_map(
        latitude=input.latitude,
        longitude=input.longitude,
        incident_id=incident_id,
        corridor=data["corridor"],
        event_type=data["event_type"],
        priority_label=priority["label"],
        risk_level=risk["level"],
    )

    # --- Save to DB ---
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

    # --- Build response ---
    return SimplifiedAnalyzeResponse(
        incident_id=incident_id,
        location=LocationInfo(
            corridor=location["corridor"],
            corridor_name=location["corridor_name"],
            police_station=location["police_station"],
            police_station_name=location.get("police_station_name"),
            police_station_address=location.get("police_station_address"),
            distance_km_approx=location["distance_km_approx"],
        ),
        inferred=InferredFields(
            event_type=event_type,
            event_type_label=get_label(EVENT_TYPE, event_type),
            veh_type=veh_type,
            veh_type_label=get_label(VEHICLE_TYPE, veh_type),
            hour=data["hour"],
            day_of_week=data["day_of_week"],
            month=data["month"],
            corridor=location["corridor"],
            corridor_name=location["corridor_name"],
            police_station=location["police_station"],
        ),
        priority=priority,
        road_closure=road_closure,
        risk=risk,
        recommendation=recommendation,
        similar_incidents=similar,
        diversion_map_url=f"/maps/{incident_id}.html",
    )
