"""
Routing Service — Incident-aware route calculation.

Fetches multiple driving routes from OSRM (free, no API key), scores each
against active incident zones using haversine distance, and returns the best
(safest) route. Map visualization still uses Mappls SDK.
"""

import math
import requests
from datetime import datetime

from app.config import MAPMYINDIA_API_KEY, MAPS_DIR
from app.database import get_active_incidents


# ─── Haversine Distance ─────────────────────────────────────────

def haversine(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Calculate distance in meters between two lat/lon points."""
    R = 6371000  # Earth radius in meters
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    d_phi = math.radians(lat2 - lat1)
    d_lambda = math.radians(lon2 - lon1)
    a = math.sin(d_phi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(d_lambda / 2) ** 2
    return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))


# ─── Decode Polyline ─────────────────────────────────────────────

def decode_polyline(encoded: str) -> list[list[float]]:
    """Decode a Google-style encoded polyline string into [[lat, lon], ...]."""
    coords = []
    index = 0
    lat = 0
    lng = 0

    while index < len(encoded):
        # Decode latitude
        shift = 0
        result = 0
        while True:
            b = ord(encoded[index]) - 63
            index += 1
            result |= (b & 0x1F) << shift
            shift += 5
            if b < 0x20:
                break
        lat += (~(result >> 1) if (result & 1) else (result >> 1))

        # Decode longitude
        shift = 0
        result = 0
        while True:
            b = ord(encoded[index]) - 63
            index += 1
            result |= (b & 0x1F) << shift
            shift += 5
            if b < 0x20:
                break
        lng += (~(result >> 1) if (result & 1) else (result >> 1))

        coords.append([lat / 1e5, lng / 1e5])

    return coords


# ─── Fetch Routes from Mappls ────────────────────────────────────

def fetch_routes(origin_lat: float, origin_lon: float, dest_lat: float, dest_lon: float) -> list[dict]:
    """
    Call OSRM (Open Source Routing Machine) public API to get driving routes
    with alternatives. Free, no API key needed.
    Returns a list of route dicts, each with 'coordinates', 'distance_m', 'duration_s'.
    """
    url = (
        f"https://router.project-osrm.org/route/v1/driving/"
        f"{origin_lon},{origin_lat};{dest_lon},{dest_lat}"
    )
    params = {
        "geometries": "polyline",
        "overview": "full",
        "alternatives": "true",
        "steps": "true",
    }

    import time
    max_retries = 3
    for attempt in range(max_retries):
        try:
            resp = requests.get(url, params=params, timeout=15)

            if resp.status_code >= 500 and attempt < max_retries - 1:
                print(f"[WARN] OSRM returned {resp.status_code}, retrying ({attempt + 1}/{max_retries})...")
                time.sleep(0.5)
                continue

            resp.raise_for_status()
            data = resp.json()

            if data.get("code") != "Ok":
                raise RuntimeError(f"OSRM error: {data.get('code')} - {data.get('message', 'Unknown')}")

            routes = []
            for route in data.get("routes", []):
                coords = decode_polyline(route["geometry"])
                routes.append({
                    "coordinates": coords,
                    "distance_m": route["distance"],
                    "duration_s": route["duration"],
                })
            return routes

        except requests.exceptions.RequestException as e:
            if attempt < max_retries - 1:
                print(f"[WARN] OSRM attempt {attempt + 1} failed: {e}, retrying...")
                time.sleep(0.5)
                continue
            raise RuntimeError(f"OSRM API failed after {max_retries} attempts: {e}")



# ─── Score Routes Against Incidents ──────────────────────────────

INCIDENT_ZONE_RADIUS_M = 500  # meters

def score_route(route_coords: list[list[float]], incidents: list[dict]) -> tuple[float, list[dict]]:
    """
    Score a route against active incidents.
    Returns (total_score, list of incidents crossed).
    Lower score = better route.
    """
    total_score = 0.0
    incidents_crossed = []

    for inc in incidents:
        inc_lat = inc["latitude"]
        inc_lon = inc["longitude"]
        is_high = inc.get("priority", 0) == 1
        is_closed = inc.get("road_closure", 0) == 1

        # Find minimum distance from any route point to this incident
        min_dist = float("inf")
        for pt in route_coords:
            d = haversine(pt[0], pt[1], inc_lat, inc_lon)
            min_dist = min(min_dist, d)
            if d < 50:  # early exit — definitely intersects
                break

        if min_dist < INCIDENT_ZONE_RADIUS_M:
            if is_closed:
                penalty = 1000.0
            elif is_high:
                penalty = 100.0
            else:
                penalty = 5.0

            total_score += penalty
            incidents_crossed.append({
                "incident_id": inc["id"],
                "priority": "HIGH" if is_high else "LOW",
                "proximity_meters": round(min_dist, 1),
            })

    return total_score, incidents_crossed


# ─── Main Orchestrator ───────────────────────────────────────────

def find_best_route(origin_lat: float, origin_lon: float, dest_lat: float, dest_lon: float) -> dict:
    """
    Find the best driving route from origin to destination,
    avoiding or minimizing exposure to active incident zones.
    """
    # 1. Fetch active incidents
    incidents = get_active_incidents()

    # 2. Fetch route alternatives from Mappls
    routes = fetch_routes(origin_lat, origin_lon, dest_lat, dest_lon)
    if not routes:
        raise RuntimeError("No routes returned from OSRM routing API")

    # 3. Score each route
    best_route = None
    best_score = float("inf")
    best_incidents = []

    for route in routes:
        score, crossed = score_route(route["coordinates"], incidents)
        if score < best_score:
            best_score = score
            best_route = route
            best_incidents = crossed

    # 4. Build warnings
    warnings = []
    if best_incidents:
        high_count = sum(1 for i in best_incidents if i["priority"] == "HIGH")
        low_count = sum(1 for i in best_incidents if i["priority"] == "LOW")
        if high_count:
            warnings.append(f"Route passes near {high_count} HIGH-priority incident(s)")
        if low_count:
            warnings.append(f"Route passes near {low_count} LOW-priority incident(s)")

    # 5. Generate route ID and map
    route_id = f"ROUTE-{datetime.now().strftime('%Y%m%d-%H%M%S')}"

    map_html = generate_route_map(
        route_coords=best_route["coordinates"],
        incidents=incidents,
        incidents_on_route=best_incidents,
        route_id=route_id,
        origin=(origin_lat, origin_lon),
        destination=(dest_lat, dest_lon),
    )

    # Save map to file
    map_path = MAPS_DIR / f"{route_id}.html"
    with open(map_path, "w", encoding="utf-8") as f:
        f.write(map_html)

    return {
        "route_id": route_id,
        "distance_km": round(best_route["distance_m"] / 1000, 2),
        "duration_minutes": round(best_route["duration_s"] / 60, 1),
        "route_coordinates": best_route["coordinates"],
        "incidents_on_route": best_incidents,
        "is_clean_route": len(best_incidents) == 0,
        "warnings": warnings,
        "map_url": f"/maps/{route_id}.html",
        "alternatives_checked": len(routes),
    }


# ─── Map Generation ─────────────────────────────────────────────

def generate_route_map(
    route_coords: list[list[float]],
    incidents: list[dict],
    incidents_on_route: list[dict],
    route_id: str,
    origin: tuple,
    destination: tuple,
) -> str:
    """Generate an HTML map showing the route polyline and incident zones."""

    # Build the route polyline as JS array
    polyline_js = ",\n".join(
        f"                {{lat: {pt[0]}, lng: {pt[1]}}}"
        for pt in route_coords
    )

    # Build incident markers JS
    incident_markers_js = ""
    for inc in incidents:
        is_high = inc.get("priority", 0) == 1
        is_closed = inc.get("road_closure", 0) == 1
        color = "#FF0000" if (is_high or is_closed) else "#FFA500"
        radius = 200 if is_high else 500
        label = f"HIGH (Closed)" if is_closed else ("HIGH" if is_high else "LOW")

        incident_markers_js += f"""
            new mappls.Circle({{
                map: map,
                center: {{lat: {inc['latitude']}, lng: {inc['longitude']}}},
                radius: {radius},
                fillColor: '{color}',
                fillOpacity: 0.2,
                strokeColor: '{color}',
                strokeOpacity: 0.8,
                strokeWeight: 2
            }});
            new mappls.Marker({{
                map: map,
                position: {{lat: {inc['latitude']}, lng: {inc['longitude']}}},
                fitbounds: false,
                popupHtml: '<b>Incident: {inc["id"]}</b><br/>Priority: {label}'
            }});
"""

    # Determine SDK URL
    sdk_url = f"https://sdk.mappls.com/map/sdk/web?v=3.0&access_token={MAPMYINDIA_API_KEY}"

    # Calculate map center
    center_lat = (origin[0] + destination[0]) / 2
    center_lon = (origin[1] + destination[1]) / 2

    html = f"""<!DOCTYPE html>
<html>
<head>
    <title>ARES Route Map - {route_id}</title>
    <meta name="viewport" content="initial-scale=1.0, user-scalable=no" />
    <style>
        html, body, #map {{ margin: 0; padding: 0; width: 100%; height: 100%; }}
        .route-legend {{
            position: absolute; bottom: 20px; left: 20px; z-index: 999;
            background: rgba(0,0,0,0.8); color: white; padding: 12px 16px;
            border-radius: 8px; font-family: sans-serif; font-size: 13px;
            line-height: 1.6;
        }}
        .route-legend .dot {{
            display: inline-block; width: 10px; height: 10px;
            border-radius: 50%; margin-right: 6px;
        }}
    </style>
    <script src="{sdk_url}"></script>
</head>
<body>
    <div id="map"></div>
    <div class="route-legend">
        <b>ARES Route: {route_id}</b><br/>
        <span class="dot" style="background:#2196F3"></span> Optimal Route<br/>
        <span class="dot" style="background:#FF0000"></span> HIGH Priority Incident<br/>
        <span class="dot" style="background:#FFA500"></span> LOW Priority Incident<br/>
        <span class="dot" style="background:#4CAF50"></span> Origin<br/>
        <span class="dot" style="background:#F44336"></span> Destination
    </div>
    <script>
        var map = new mappls.Map('map', {{
            center: [{center_lat}, {center_lon}],
            zoom: 13
        }});

        map.addListener('load', function() {{
            // Origin marker (green)
            new mappls.Marker({{
                map: map,
                position: {{lat: {origin[0]}, lng: {origin[1]}}},
                fitbounds: false,
                popupHtml: '<b>Origin</b>'
            }});

            // Destination marker (red)
            new mappls.Marker({{
                map: map,
                position: {{lat: {destination[0]}, lng: {destination[1]}}},
                fitbounds: false,
                popupHtml: '<b>Destination</b>'
            }});

            // Route polyline (blue)
            new mappls.Polyline({{
                map: map,
                path: [
{polyline_js}
                ],
                strokeColor: '#2196F3',
                strokeOpacity: 0.9,
                strokeWeight: 5,
                fitbounds: true
            }});

            // Incident zone overlays
{incident_markers_js}
        }});
    </script>
</body>
</html>"""

    return html
