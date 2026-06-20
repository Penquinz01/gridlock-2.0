"""
Authentication Service — Lightweight auth helper for Bengaluru Police Station logins.
"""

from fastapi import HTTPException, Security
from fastapi.security import APIKeyHeader

# Set up simple token-based header for auth checks
api_key_header = APIKeyHeader(name="Authorization", auto_error=False)


def authenticate_station(station_id: int, password: str) -> str:
    """
    Authenticate a police station.
    For hackathon simplicity, password must be 'station_pass_<station_id>'.
    Returns a simple auth token.
    """
    expected_password = f"station_pass_{station_id}"
    if password != expected_password:
        raise HTTPException(status_code=401, detail="Invalid police station credentials")

    # Return a dummy mock token
    return f"token_station_{station_id}_auth"


def verify_token(token: str) -> int:
    """
    Verify token and return corresponding station_id.
    """
    if not token or not token.startswith("token_station_") or not token.endswith("_auth"):
        raise HTTPException(status_code=401, detail="Missing or invalid authentication token")

    try:
        parts = token.split("_")
        station_id = int(parts[2])
        return station_id
    except (ValueError, IndexError):
        raise HTTPException(status_code=401, detail="Malformed authentication token")
