"""
Pydantic Schemas — All request/response models in one file.
"""

from pydantic import BaseModel, Field
from typing import Optional


# ─── Shared ─────────────────────────────────────────────────────

class IncidentInput(BaseModel):
    """Base incident input — used by /analyze and shared across endpoints."""
    event_type: int = Field(..., ge=0, le=1, description="0=Minor, 1=Major")
    event_cause: int = Field(..., ge=0, le=16, description="Encoded cause category")
    veh_type: int = Field(..., ge=0, le=9, description="Encoded vehicle type")
    corridor: int = Field(..., ge=0, le=21, description="Encoded corridor/road")
    police_station: int = Field(..., ge=0, le=53, description="Encoded police station")
    latitude: float = Field(..., ge=12.5, le=13.5, description="Latitude (Bengaluru range)")
    longitude: float = Field(..., ge=77.0, le=78.0, description="Longitude (Bengaluru range)")
    hour: int = Field(..., ge=0, le=23, description="Hour of day (0-23)")
    day_of_week: int = Field(..., ge=0, le=6, description="Day of week (0=Mon, 6=Sun)")
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
    risk_level: str = Field(..., description="CRITICAL, HIGH, MEDIUM, or LOW")
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
    latitude: float = Field(..., ge=12.5, le=13.5)
    longitude: float = Field(..., ge=77.0, le=78.0)
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
    """Minimal input from the frontend — just location, cause, and time."""
    latitude: float = Field(..., ge=12.0, le=14.0, description="Latitude (Bengaluru range)")
    longitude: float = Field(..., ge=76.5, le=78.5, description="Longitude (Bengaluru range)")
    event_cause: int = Field(..., ge=0, le=16, description="Encoded cause category")
    time: str = Field(..., description="ISO 8601 datetime string, e.g. 2026-06-19T15:30:00")

    model_config = {"json_schema_extra": {
        "examples": [{
            "latitude": 13.04,
            "longitude": 77.518,
            "event_cause": 14,
            "time": "2026-06-19T15:30:00"
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

