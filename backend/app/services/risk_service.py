"""
Risk Service — Rule-based operational risk assessment.
"""

from app.rules.risk_rules import RISK_RULES, get_risk_level


def assess_risk(incident: dict) -> dict:
    """
    Calculate risk score and level for an incident.

    Args:
        incident: dict with keys: priority, requires_road_closure, hour,
                  event_type, veh_type, corridor

    Returns:
        {"score": int, "level": str, "factors": list[str]}
    """
    score = 0
    factors = []

    for condition_fn, points, description in RISK_RULES:
        try:
            if condition_fn(incident):
                score += points
                factors.append(description)
        except (KeyError, TypeError):
            continue  # Skip rules that can't be evaluated

    score = min(score, 100)  # Cap at 100
    level = get_risk_level(score)

    return {
        "score": score,
        "level": level,
        "factors": factors,
    }
