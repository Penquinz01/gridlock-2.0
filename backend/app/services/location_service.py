"""
Location Service — Resolve coordinates to corridor and police station.

Strategy:
  1. Find the nearest record in the preprocessed dataset using Euclidean
     distance on (latitude, longitude).
  2. Extract the corridor and police_station integer codes from that record.
  3. Optionally query MapmyIndia/Mappls Nearby Places API for a real
     police station name (falls back to dataset lookup if keys are missing
     or the API call fails).
"""

import numpy as np
import requests
from app.ml import get_dataset
from app.config import MAPMYINDIA_API_KEY, MAPMYINDIA_CLIENT_ID, MAPMYINDIA_CLIENT_SECRET

from app.utils.mappings import CORRIDOR, get_label


# ─── Dataset-based nearest-neighbor lookup ──────────────────────

def resolve_location_features(latitude: float, longitude: float) -> dict:
    """
    Find the nearest record in the dataset and return its corridor
    and police_station codes.

    Returns:
        {
            "corridor": int,
            "corridor_name": str,
            "police_station": int,
            "police_station_name": str | None,
            "distance_km_approx": float,
        }
    """
    df = get_dataset()

    coords = df[["latitude", "longitude"]].values
    query = np.array([latitude, longitude])

    # Euclidean distance (good enough for small regions like Bengaluru)
    distances = np.sqrt(np.sum((coords - query) ** 2, axis=1))
    nearest_idx = int(np.argmin(distances))
    nearest_row = df.iloc[nearest_idx]

    # Rough km conversion (1 degree ≈ 111 km at this latitude)
    approx_km = float(distances[nearest_idx]) * 111.0

    corridor_code = int(nearest_row["corridor"])
    ps_code = int(nearest_row["police_station"])

    return {
        "corridor": corridor_code,
        "corridor_name": get_label(CORRIDOR, corridor_code),
        "police_station": ps_code,
        "police_station_name": None,  # filled by MapmyIndia if available
        "distance_km_approx": round(approx_km, 2),
    }


# ─── MapmyIndia / Mappls Integration ───────────────────────────

_mappls_token: str | None = None


def _get_mappls_token() -> str | None:
    """Obtain an OAuth2 token from Mappls. Cached in module-level var."""
    global _mappls_token

    if _mappls_token:
        return _mappls_token

    if not MAPMYINDIA_CLIENT_ID or not MAPMYINDIA_CLIENT_SECRET:
        return None

    try:
        resp = requests.post(
            "https://outpost.mapmyindia.com/api/security/oauth/token",
            data={
                "grant_type": "client_credentials",
                "client_id": MAPMYINDIA_CLIENT_ID,
                "client_secret": MAPMYINDIA_CLIENT_SECRET,
            },
            timeout=5,
        )
        resp.raise_for_status()
        _mappls_token = resp.json().get("access_token")
        return _mappls_token
    except Exception as e:
        print(f"[WARN] Mappls OAuth failed: {e}")
        return None


def search_nearby_police_station(latitude: float, longitude: float) -> dict | None:
    """
    Search for nearby police stations using Mappls Nearby Places API.
    Supports either the static MAPMYINDIA_API_KEY or OAuth Bearer Token.
    Retries up to 3 times on transient server errors (503).

    Returns the closest police station dict or None on failure.
    """
    import time

    params = {
        "keywords": "police station",
        "refLocation": f"{latitude},{longitude}",
        "radius": 5000,  # 5 km radius
        "sortBy": "dist:asc",
    }
    headers = {}

    # Use static API key as query param if present
    if MAPMYINDIA_API_KEY:
        params["access_token"] = MAPMYINDIA_API_KEY
        url = "https://search.mappls.com/api/places/nearby/json"
    else:
        # Fallback to OAuth token
        token = _get_mappls_token()
        if not token:
            return None
        headers["Authorization"] = f"Bearer {token}"
        url = "https://atlas.mapmyindia.com/api/places/nearby/json"

    max_retries = 3
    for attempt in range(max_retries):
        try:
            resp = requests.get(
                url,
                params=params,
                headers=headers,
                timeout=5,
            )

            # Retry on 503 Service Unavailable
            if resp.status_code == 503 and attempt < max_retries - 1:
                print(f"[WARN] Mappls API returned 503, retrying ({attempt + 1}/{max_retries})...")
                time.sleep(0.5)
                continue

            resp.raise_for_status()
            
            try:
                data = resp.json()
            except ValueError:
                raise RuntimeError(f"API returned a non-JSON response (status: {resp.status_code})")

            results = data.get("suggestedLocations", [])
            if results:
                nearest = results[0]
                return {
                    "name": nearest.get("placeName", "Unknown"),
                    "address": nearest.get("placeAddress", ""),
                    "latitude": float(nearest.get("latitude", latitude)),
                    "longitude": float(nearest.get("longitude", longitude)),
                    "distance_meters": nearest.get("distance", 0),
                }
        except Exception as e:
            if attempt < max_retries - 1:
                print(f"[WARN] Mappls nearby search attempt {attempt + 1} failed: {e}, retrying...")
                time.sleep(0.5)
                continue
            print(f"[WARN] Mappls nearby search failed after {max_retries} attempts: {e}")



    return None



def resolve_full_location(latitude: float, longitude: float) -> dict:
    """
    High-level helper: resolve coordinates to corridor, police station,
    and optionally the real police station name via MapmyIndia.
    """
    # Step 1: Dataset-based lookup (always works)
    location = resolve_location_features(latitude, longitude)

    # Step 2: Try MapmyIndia for real police station name
    mappls_result = search_nearby_police_station(latitude, longitude)
    if mappls_result:
        location["police_station_name"] = mappls_result["name"]
        location["police_station_address"] = mappls_result.get("address", "")
        location["police_station_coords"] = {
            "latitude": mappls_result["latitude"],
            "longitude": mappls_result["longitude"],
        }

    return location
