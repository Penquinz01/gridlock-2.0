"""
Map Service — Mappls config and place search for the frontend map.
"""

import requests

from app.services.location_service import (
    BANGALORE_CENTER,
    KARNATAKA_BBOX,
    get_mappls_credentials,
)

MIN_LON, MIN_LAT, MAX_LON, MAX_LAT = KARNATAKA_BBOX


def _in_karnataka_bbox(latitude: float, longitude: float) -> bool:
    return MIN_LAT <= latitude <= MAX_LAT and MIN_LON <= longitude <= MAX_LON


def get_map_config() -> dict:
    """Return frontend map provider configuration."""
    creds = get_mappls_credentials()
    if creds:
        return {
            "provider": "mappls",
            "token": creds["token"],
            "auth_type": creds["auth_type"],
        }
    return {"provider": "osm", "token": None, "auth_type": None}


def search_places(query: str, limit: int = 15) -> list[dict]:
    """
    Search for places biased to Bangalore/Karnataka.
    Uses Mappls autosuggest when configured, otherwise Photon (OSM).
    """
    query = query.strip()
    if not query:
        return []

    creds = get_mappls_credentials()
    if creds:
        return _search_mappls(query, limit, creds)
    return _search_photon(query, limit)


def _search_mappls(query: str, limit: int, creds: dict) -> list[dict]:
    lat, lng = BANGALORE_CENTER
    params = {
        "query": query,
        "location": f"{lat},{lng}",
        "zoom": 12,
        "filter": f"bounds:{MIN_LAT},{MIN_LON};{MAX_LAT},{MAX_LON}",
    }
    headers = {}

    if creds["auth_type"] == "rest_key":
        params["access_token"] = creds["token"]
        url = "https://search.mappls.com/search/places/autosuggest/json"
    else:
        headers["Authorization"] = f"Bearer {creds['token']}"
        url = "https://atlas.mapmyindia.com/api/places/search/json"

    try:
        resp = requests.get(url, params=params, headers=headers, timeout=8)
        resp.raise_for_status()
        data = resp.json()
    except Exception as e:
        print(f"[WARN] Mappls autosuggest failed: {e}")
        return _search_photon(query, limit)

    suggestions = []
    locations = data.get("suggestedLocations", [])
    for item in locations:
        if len(suggestions) >= limit:
            break

        name = item.get("placeName") or item.get("placeAddress") or query
        address = item.get("placeAddress") or item.get("formattedAddress") or ""
        latitude = item.get("latitude") or item.get("lat")
        longitude = item.get("longitude") or item.get("lng")

        if latitude is None or longitude is None:
            eloc = item.get("eLoc") or item.get("mapplsPin")
            if eloc:
                coords = _get_mappls_place_coordinates(eloc, creds)
                if coords:
                    latitude, longitude = coords

        try:
            latitude = float(latitude)
            longitude = float(longitude)
        except (TypeError, ValueError):
            continue

        if not _in_karnataka_bbox(latitude, longitude):
            continue

        suggestions.append({
            "name": name,
            "address": address,
            "latitude": latitude,
            "longitude": longitude,
        })

    if suggestions:
        return suggestions

    nearby_results = _search_mappls_nearby(query, limit, creds)
    if nearby_results:
        return nearby_results

    return _search_photon(query, limit)


def _get_mappls_place_coordinates(eloc: str, creds: dict) -> tuple[float, float] | None:
    """Resolve Mappls eLoc to latitude/longitude via place details API."""
    headers = {}
    params = {}

    if creds["auth_type"] == "rest_key":
        params["access_token"] = creds["token"]
        url = f"https://place.mappls.com/O2O/entity/place-details/{eloc}"
    else:
        headers["Authorization"] = f"Bearer {creds['token']}"
        url = f"https://atlas.mapmyindia.com/api/places/eloc/{eloc}"

    try:
        resp = requests.get(url, params=params, headers=headers, timeout=8)
        resp.raise_for_status()
        data = resp.json()
    except Exception as e:
        print(f"[WARN] Mappls place details failed for {eloc}: {e}")
        return None

    latitude = data.get("latitude") or data.get("lat")
    longitude = data.get("longitude") or data.get("lng") or data.get("lon")

    try:
        latitude = float(latitude)
        longitude = float(longitude)
    except (TypeError, ValueError):
        return None

    if latitude == 0 and longitude == 0:
        return None

    return latitude, longitude


def _search_mappls_nearby(query: str, limit: int, creds: dict) -> list[dict]:
    """Fallback search using Mappls nearby API, which returns coordinates."""
    import time

    lat, lng = BANGALORE_CENTER
    params = {
        "keywords": query,
        "refLocation": f"{lat},{lng}",
        "radius": 50000,
        "sortBy": "dist:asc",
    }
    headers = {}

    if creds["auth_type"] == "rest_key":
        params["access_token"] = creds["token"]
        url = "https://search.mappls.com/api/places/nearby/json"
    else:
        token = creds["token"]
        if not token:
            return []
        headers["Authorization"] = f"Bearer {token}"
        url = "https://atlas.mapmyindia.com/api/places/nearby/json"

    max_retries = 3
    for attempt in range(max_retries):
        try:
            resp = requests.get(url, params=params, headers=headers, timeout=8)
            if resp.status_code == 503 and attempt < max_retries - 1:
                time.sleep(0.5)
                continue
            resp.raise_for_status()
            data = resp.json()
            break
        except Exception as e:
            if attempt < max_retries - 1:
                time.sleep(0.5)
                continue
            print(f"[WARN] Mappls nearby search failed: {e}")
            return []
    else:
        return []

    suggestions = []
    for item in data.get("suggestedLocations", []):
        try:
            latitude = float(item.get("latitude") or item.get("lat"))
            longitude = float(item.get("longitude") or item.get("lng"))
        except (TypeError, ValueError):
            continue

        if not _in_karnataka_bbox(latitude, longitude):
            continue

        suggestions.append({
            "name": item.get("placeName") or query,
            "address": item.get("placeAddress") or "",
            "latitude": latitude,
            "longitude": longitude,
        })
        if len(suggestions) >= limit:
            break

    return suggestions


def _search_photon(query: str, limit: int) -> list[dict]:
    lat, lng = BANGALORE_CENTER
    params = {
        "q": query,
        "limit": limit,
        "lat": lat,
        "lon": lng,
        "bbox": f"{MIN_LON},{MIN_LAT},{MAX_LON},{MAX_LAT}",
    }

    headers = {
        "User-Agent": "Mozilla/5.0"
    }

    try:
        resp = requests.get("https://photon.komoot.io/api/", params=params, headers=headers, timeout=8)
        resp.raise_for_status()
        data = resp.json()
    except Exception as e:
        print(f"[WARN] Photon search failed: {e}")
        return []

    suggestions = []
    for feature in data.get("features", []):
        coords = feature.get("geometry", {}).get("coordinates", [])
        if len(coords) < 2:
            continue

        longitude, latitude = float(coords[0]), float(coords[1])
        if not _in_karnataka_bbox(latitude, longitude):
            continue

        props = feature.get("properties", {})
        name = props.get("name") or query
        address_parts = [
            props.get("street"),
            props.get("city"),
            props.get("state"),
            props.get("country"),
        ]
        address = ", ".join(part for part in address_parts if part)
        suggestions.append({
            "name": name,
            "address": address,
            "latitude": latitude,
            "longitude": longitude,
        })
        if len(suggestions) >= limit:
            break

    return suggestions
