"""
Risk Route — POST /risk

Standalone risk assessment endpoint.
"""

from fastapi import APIRouter
from app.schemas import RiskInput, RiskResult
from app.services import risk_service

router = APIRouter(tags=["Risk"])


@router.post("/risk", response_model=RiskResult)
def assess_risk(data: RiskInput):
    """Assess operational risk for an incident using rule-based scoring."""
    result = risk_service.assess_risk(data.model_dump())
    return RiskResult(**result)
