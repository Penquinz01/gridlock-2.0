"""
Route Route — POST /route

Calculates the best driving route between two points,
avoiding or minimizing exposure to active incident zones.
"""

from fastapi import APIRouter, HTTPException
from app.schemas import RouteInput, RouteResponse
from app.services.routing_service import find_best_route

router = APIRouter(tags=["Routing"])


@router.post("/route", response_model=RouteResponse)
def calculate_route(input: RouteInput):
    """
    Find the best incident-aware driving route.

    1. Fetches 2-3 alternative routes from Mappls Directions API
    2. Scores each route against active incident zones
    3. Returns the route with least incident exposure

    If a clean route exists, it is always preferred.
    If all routes cross incidents, the one crossing lowest-priority incidents wins.
    """
    try:
        result = find_best_route(
            origin_lat=input.origin.latitude,
            origin_lon=input.origin.longitude,
            dest_lat=input.destination.latitude,
            dest_lon=input.destination.longitude,
        )
        return RouteResponse(**result)
    except RuntimeError as e:
        raise HTTPException(status_code=502, detail=str(e))
