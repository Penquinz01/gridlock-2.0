"""
Map Routes — GET /api/map/config, GET /api/map/search
"""

from fastapi import APIRouter, Query

from app.schemas import MapConfigResponse, MapSearchResponse, MapSearchSuggestion
from app.services import map_service

router = APIRouter(prefix="/api/map", tags=["Map"])


@router.get("/config", response_model=MapConfigResponse)
def get_map_config():
    """Return map provider configuration for the frontend."""
    return MapConfigResponse(**map_service.get_map_config())


@router.get("/search", response_model=MapSearchResponse)
def search_places(
    q: str = Query(..., min_length=1, description="Search query"),
    limit: int = Query(15, ge=1, le=25, description="Max suggestions to return"),
):
    """Search for places biased to Bangalore/Karnataka."""
    suggestions = map_service.search_places(q, limit=limit)
    return MapSearchResponse(
        suggestions=[MapSearchSuggestion(**item) for item in suggestions]
    )
