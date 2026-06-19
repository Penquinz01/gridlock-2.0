"""
Diversion Route — POST /diversion

Generate a Folium diversion/incident map.
"""

from fastapi import APIRouter
from app.schemas import DiversionInput, DiversionResponse
from app.services import diversion_service

router = APIRouter(tags=["Diversion"])


@router.post("/diversion", response_model=DiversionResponse)
def generate_diversion_map(data: DiversionInput):
    """Generate a Folium map showing the incident location and impact zones."""
    map_html = diversion_service.generate_diversion_map(
        latitude=data.latitude,
        longitude=data.longitude,
        incident_id=data.incident_id,
    )
    return DiversionResponse(
        map_html=map_html,
        incident_location={
            "latitude": data.latitude,
            "longitude": data.longitude,
        },
    )
