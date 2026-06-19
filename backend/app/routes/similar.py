"""
Similar Incidents Route — POST /similar-incidents

Find similar past incidents using KNN.
"""

from fastapi import APIRouter
from app.schemas import SimilarIncidentInput, SimilarIncidentResponse
from app.services import similarity_service

router = APIRouter(tags=["Similarity"])


@router.post("/similar-incidents", response_model=SimilarIncidentResponse)
def find_similar_incidents(data: SimilarIncidentInput):
    """Find similar incidents from historical data using KNN."""
    results = similarity_service.find_similar(
        features=data.model_dump(),
        top_k=data.top_k,
    )
    return SimilarIncidentResponse(
        similar_incidents=results,
        count=len(results),
    )
