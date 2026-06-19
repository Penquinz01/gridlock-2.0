"""
Hotspots Route — GET /hotspots

Incident hotspot analytics with optional filters.
"""

from typing import Optional
from fastapi import APIRouter, Query
from app.schemas import HotspotResponse
from app.services import hotspot_service

router = APIRouter(tags=["Hotspots"])


@router.get("/hotspots", response_model=HotspotResponse)
def get_hotspots(
    hour: Optional[int] = Query(None, ge=0, le=23, description="Filter by hour (0-23)"),
    day_of_week: Optional[int] = Query(None, ge=0, le=6, description="Filter by day (0=Mon)"),
    month: Optional[int] = Query(None, ge=1, le=12, description="Filter by month (1-12)"),
    event_type: Optional[int] = Query(None, ge=0, le=1, description="Filter by event type"),
    top_n: int = Query(20, ge=1, le=100, description="Max hotspots to return"),
):
    """Get incident hotspots with optional time and type filters."""
    result = hotspot_service.get_hotspots(
        hour=hour,
        day_of_week=day_of_week,
        month=month,
        event_type=event_type,
        top_n=top_n,
    )
    return HotspotResponse(**result)
