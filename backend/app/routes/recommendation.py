"""
Recommendation Route — POST /recommendation

Standalone resource recommendation endpoint.
"""

from fastapi import APIRouter
from app.schemas import RecommendationInput, RecommendationResult
from app.services import recommendation_service

router = APIRouter(tags=["Recommendation"])


@router.post("/recommendation", response_model=RecommendationResult)
def get_recommendation(data: RecommendationInput):
    """Get resource allocation recommendations based on risk level."""
    result = recommendation_service.get_recommendation(
        risk_level=data.risk_level,
        incident=data.model_dump(),
    )
    return RecommendationResult(**result)
