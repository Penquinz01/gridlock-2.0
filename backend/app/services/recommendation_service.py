"""
Recommendation Service — Resource allocation recommendations.
"""

from app.rules.recommendation_rules import RESOURCE_TABLE, CONDITIONAL_NOTES


def get_recommendation(risk_level: str, incident: dict = None) -> dict:
    """
    Get resource recommendations based on risk level.

    Args:
        risk_level: "CRITICAL", "HIGH", "MEDIUM", or "LOW"
        incident: optional dict with incident details for conditional notes

    Returns:
        {"officers": int, "barricades": int, "escalation": str, "additional_notes": list[str]}
    """
    # Look up base recommendation
    base = RESOURCE_TABLE.get(risk_level, RESOURCE_TABLE["LOW"])


    notes = list(base["notes"])  # Copy to avoid mutating the rule table

    # Add conditional notes if incident data is provided
    if incident:
        for condition_fn, note in CONDITIONAL_NOTES:
            try:
                if condition_fn(incident):
                    notes.append(note)
            except (KeyError, TypeError):
                continue

    return {
        "officers": base["officers"],
        "barricades": base["barricades"],
        "escalation": base["escalation"],
        "additional_notes": notes,
    }
