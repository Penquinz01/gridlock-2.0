"""
Pydantic Schemas — All request/response models in one file.
"""

from pydantic import BaseModel, Field
from typing import Optional


# ─── Shared ─────────────────────────────────────────────────────

class IncidentInput(BaseModel):
    """Base incident input — used by /analyze and shared across endpoints."""
    event_type: int = Field(..., ge=0, le=1, description="0=Planned, 1=Unplanned")
    event_cause: int = Field(..., ge=0, le=16, description="Encoded cause: 0=Debris, 1=Fog, 2=Accident, 3=Congestion, 4=Construction, 5=Debris, 6=Others, 7=Pot Holes, 8=Procession, 9=Protest, 10=Public Event, 11=Road Conditions, 12=Test/Demo, 13=Tree Fall, 14=Vehicle Breakdown, 15=VIP Movement, 16=Water Logging")
    veh_type: int = Field(..., ge=0, le=10, description="Encoded vehicle: 0=Auto, 1=BMTC Bus, 2=Heavy Vehicle, 3=KSRTC Bus, 4=LCV, 5=Others, 6=Private Bus, 7=Private Car, 8=Taxi, 9=Truck, 10=Unknown")
    corridor: int = Field(..., ge=0, le=22, description="Encoded corridor/road (0-22)")
    police_station: int = Field(..., ge=0, le=53, description="Encoded police station (0-53)")
    latitude: float = Field(..., ge=12.7, le=13.4, description="Latitude (Bengaluru district: ~12.7 to ~13.4)")
    longitude: float = Field(..., ge=77.2, le=77.9, description="Longitude (Bengaluru district: ~77.2 to ~77.9)")
    hour: int = Field(..., ge=0, le=23, description="Hour of day (0-23)")
    day_of_week: int = Field(..., ge=0, le=6, description="Day of week (0=Friday, 1=Monday, 2=Saturday, 3=Sunday, 4=Thursday, 5=Tuesday, 6=Wednesday)")
    month: int = Field(..., ge=1, le=12, description="Month (1-12)")

    model_config = {"json_schema_extra": {
        "examples": [{
            "event_type": 1, "event_cause": 14, "veh_type": 4,
            "corridor": 19, "police_station": 39,
            "latitude": 13.04, "longitude": 77.518,
            "hour": 17, "day_of_week": 4, "month": 3
        }]
    }}


# ─── Priority ──────────────────────────────────────────────────

class PriorityResult(BaseModel):
    label: str = Field(..., description="HIGH or LOW")
    confidence: float = Field(..., description="Model confidence 0-1")


# ─── Road Closure ──────────────────────────────────────────────

class RoadClosureResult(BaseModel):
    required: bool
    confidence: float


# ─── Risk ──────────────────────────────────────────────────────

class RiskInput(BaseModel):
    event_type: int = Field(..., ge=0, le=1)
    priority: int = Field(..., ge=0, le=1)
    requires_road_closure: int = Field(..., ge=0, le=1)
    hour: int = Field(..., ge=0, le=23)
    corridor: int = Field(..., ge=0, le=21)
    veh_type: int = Field(..., ge=0, le=9)

    model_config = {"json_schema_extra": {
        "examples": [{
            "event_type": 1, "priority": 1, "requires_road_closure": 1,
            "hour": 17, "corridor": 19, "veh_type": 4
        }]
    }}


class RiskResult(BaseModel):
    score: int = Field(..., ge=0, le=100)
    level: str
    factors: list[str]


# ─── Recommendation ────────────────────────────────────────────

class RecommendationInput(BaseModel):
    risk_level: str = Field(..., description="HIGH or LOW")
    event_type: int = Field(..., ge=0, le=1)
    requires_road_closure: int = Field(..., ge=0, le=1)
    priority: int = Field(..., ge=0, le=1)

    model_config = {"json_schema_extra": {
        "examples": [{
            "risk_level": "HIGH", "event_type": 1,
            "requires_road_closure": 1, "priority": 1
        }]
    }}


class RecommendationResult(BaseModel):
    officers: int
    barricades: int
    escalation: str
    additional_notes: list[str]


# ─── Similarity ────────────────────────────────────────────────

class SimilarIncidentInput(BaseModel):
    event_type: int = Field(..., ge=0, le=1)
    event_cause: int = Field(..., ge=0, le=16)
    veh_type: int = Field(..., ge=0, le=9)
    corridor: int = Field(..., ge=0, le=21)
    hour: int = Field(..., ge=0, le=23)
    day_of_week: int = Field(..., ge=0, le=6)
    month: int = Field(..., ge=1, le=12)
    top_k: int = Field(default=5, ge=1, le=20, description="Number of similar incidents")

    model_config = {"json_schema_extra": {
        "examples": [{
            "event_type": 1, "event_cause": 14, "veh_type": 4,
            "corridor": 19, "hour": 17, "day_of_week": 4, "month": 3,
            "top_k": 5
        }]
    }}


class SimilarIncident(BaseModel):
    rank: int
    distance: float
    event_type: int
    event_cause: int
    veh_type: int
    corridor: int
    priority: int
    requires_road_closure: int
    police_station: int
    latitude: float
    longitude: float
    hour: int
    day_of_week: int
    month: int


class SimilarIncidentResponse(BaseModel):
    similar_incidents: list[SimilarIncident]
    count: int


# ─── Hotspots ──────────────────────────────────────────────────

class Hotspot(BaseModel):
    latitude: float
    longitude: float
    corridor: int
    incident_count: int
    high_priority_pct: float


class HotspotResponse(BaseModel):
    total_incidents: int
    hotspots: list[Hotspot]
    filters_applied: dict


# ─── Diversion ─────────────────────────────────────────────────

class DiversionInput(BaseModel):
    latitude: float = Field(..., ge=12.7, le=13.4, description="Latitude (Bengaluru district)")
    longitude: float = Field(..., ge=77.2, le=77.9, description="Longitude (Bengaluru district)")
    incident_id: Optional[str] = None

    model_config = {"json_schema_extra": {
        "examples": [{"latitude": 13.04, "longitude": 77.518, "incident_id": "INC-20260619-001"}]
    }}


class DiversionResponse(BaseModel):
    map_html: str = Field(..., description="Folium map as HTML string")
    incident_location: dict


# ─── Full Analyze ──────────────────────────────────────────────

class AnalyzeResponse(BaseModel):
    incident_id: str
    priority: PriorityResult
    road_closure: RoadClosureResult
    risk: RiskResult
    recommendation: RecommendationResult
    similar_incidents: list[SimilarIncident]
    diversion_map_url: str


# ─── Health ────────────────────────────────────────────────────

class HealthResponse(BaseModel):
    status: str
    models_loaded: bool
    dataset_rows: int
    db_connected: bool


# ─── Simplified Frontend Input ─────────────────────────────────

class SimplifiedIncidentInput(BaseModel):
    """Minimal input from the frontend — location, cause, time, optional vehicle type, and description."""
    latitude: float = Field(..., ge=12.7, le=13.4, description="Latitude (Bengaluru district: ~12.7 to ~13.4)")
    longitude: float = Field(..., ge=77.2, le=77.9, description="Longitude (Bengaluru district: ~77.2 to ~77.9)")

    event_cause: int = Field(..., ge=0, le=17, description="Encoded cause category (0 to 17)")
    time: str = Field(..., description="ISO 8601 datetime string, e.g. 2026-06-19T15:30:00")
    veh_type: Optional[int] = Field(None, ge=0, le=9, description="Optional encoded vehicle type if cause involves vehicles")
    description: Optional[str] = Field(None, description="Custom description if event_cause is 17 (Other)")

    model_config = {"json_schema_extra": {
        "examples": [{
            "latitude": 13.04,
            "longitude": 77.518,
            "event_cause": 17,
            "time": "2026-06-19T15:30:00",
            "veh_type": 2,
            "description": "A massive sinkhole has blocked the entire road."
        }]
    }}


class LocationInfo(BaseModel):
    """Resolved location details."""
    corridor: int
    corridor_name: str
    police_station: int
    police_station_name: Optional[str] = None
    police_station_address: Optional[str] = None
    distance_km_approx: float


class InferredFields(BaseModel):
    """Fields auto-inferred by the backend."""
    event_type: int
    event_type_label: str
    event_cause: int
    event_cause_label: str
    veh_type: int
    veh_type_label: str
    hour: int
    day_of_week: int
    month: int
    corridor: int
    corridor_name: str
    police_station: int


class SimplifiedAnalyzeResponse(BaseModel):
    """Full response from the simplified /report endpoint."""
    incident_id: str
    location: LocationInfo
    inferred: InferredFields
    priority: PriorityResult
    road_closure: RoadClosureResult
    risk: RiskResult
    recommendation: RecommendationResult
    similar_incidents: list[SimilarIncident]
    diversion_map_url: str


# ─── Police Station Portal ─────────────────────────────────────

class LoginRequest(BaseModel):
    police_station: int = Field(..., ge=0, le=53, description="Encoded police station ID")
    password: str = Field(..., description="Credentials for login")

    model_config = {"json_schema_extra": {
        "examples": [{"police_station": 39, "password": "station_pass_39"}]
    }}


class LoginResponse(BaseModel):
    success: bool
    token: str
    station_id: int
    station_name: str


class FeedbackInput(BaseModel):
    actual_officers: int = Field(..., ge=0, description="Actual number of officers deployed")
    actual_barricades: int = Field(..., ge=0, description="Actual number of barricades used")
    actual_road_closure: int = Field(..., ge=0, le=1, description="Was road closure actually needed? (0=No, 1=Yes)")
    actual_priority: int = Field(..., ge=0, le=1, description="Was it actually high priority? (0=Low, 1=High)")
    feedback_notes: Optional[str] = Field(None, description="Post-incident retrospective notes")


class FeedbackResponse(BaseModel):
    success: bool
    incident_id: str
    status: str = "RESOLVED"


