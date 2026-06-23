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


def distance_to_route_segment_m(
    point_lat: float,
    point_lon: float,
    start_lat: float,
    start_lon: float,
    end_lat: float,
    end_lon: float,
) -> float:
    """Approximate shortest distance from a point to a route segment in meters."""
    mean_lat_rad = math.radians((point_lat + start_lat + end_lat) / 3)
    meters_per_degree_lat = 111_320
    meters_per_degree_lon = 111_320 * math.cos(mean_lat_rad)

    point_x = point_lon * meters_per_degree_lon
    point_y = point_lat * meters_per_degree_lat
    start_x = start_lon * meters_per_degree_lon
    start_y = start_lat * meters_per_degree_lat
    end_x = end_lon * meters_per_degree_lon
    end_y = end_lat * meters_per_degree_lat

    segment_x = end_x - start_x
    segment_y = end_y - start_y
    segment_len_sq = segment_x * segment_x + segment_y * segment_y

    if segment_len_sq == 0:
        return math.hypot(point_x - start_x, point_y - start_y)

    t = ((point_x - start_x) * segment_x + (point_y - start_y) * segment_y) / segment_len_sq
    t = max(0, min(1, t))
    closest_x = start_x + t * segment_x
    closest_y = start_y + t * segment_y
    return math.hypot(point_x - closest_x, point_y - closest_y)


def min_distance_to_route_m(route_coords: list[list[float]], lat: float, lon: float) -> float:
    """Find the shortest distance from a coordinate to the route polyline."""
    if not route_coords:
        return float("inf")

    min_dist = min(haversine(pt[0], pt[1], lat, lon) for pt in route_coords)
    for start, end in zip(route_coords, route_coords[1:]):
        min_dist = min(
            min_dist,
            distance_to_route_segment_m(lat, lon, start[0], start[1], end[0], end[1]),
        )
        if min_dist < 50:
            break

    return min_dist


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
    Call Mappls Directions API to get driving routes with alternatives.
    Falls back to public OSRM API if Mappls fails (e.g. key issue or quota limits).
    Returns a list of route dicts, each with 'coordinates', 'distance_m', 'duration_s'.
    """
    # 1. Try Mappls first
    if MAPMYINDIA_API_KEY:
        mappls_url = (
            f"https://route.mappls.com/route/direction/route_adv/driving/"
            f"{origin_lon},{origin_lat};{dest_lon},{dest_lat}"
        )
        mappls_params = {
            "access_token": MAPMYINDIA_API_KEY,
            "geometries": "polyline",
            "overview": "full",
            "alternatives": "true",
            "steps": "true",
        }
        try:
            print(f"[INFO] Fetching routes from Mappls Directions API...")
            resp = requests.get(mappls_url, params=mappls_params, timeout=10)
            # If the response is not successful or has error codes, raise an error to trigger fallback
            resp.raise_for_status()
            data = resp.json()
            
            if "routes" in data and len(data["routes"]) > 0:
                routes = []
                for route in data.get("routes", []):
                    coords = decode_polyline(route["geometry"])
                    routes.append({
                        "coordinates": coords,
                        "distance_m": route["distance"],
                        "duration_s": route["duration"],
                    })
                print(f"[INFO] Successfully retrieved {len(routes)} routes from Mappls.")
                return routes
            else:
                print(f"[WARN] Mappls response did not contain routes: {data}")
        except Exception as e:
            print(f"[WARN] Mappls routing failed: {e}. Falling back to OSRM...")

    # 2. Fallback to OSRM
    print(f"[INFO] Fetching routes from OSRM...")
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
MAX_CLEAN_ROUTE_DISTANCE_RATIO = 1.30
MAX_CLEAN_ROUTE_DISTANCE_EXTRA_M = 5000

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

        min_dist = min_distance_to_route_m(route_coords, inc_lat, inc_lon)

        if min_dist < INCIDENT_ZONE_RADIUS_M:
            if is_closed:
                penalty = 1000.0
            elif is_high:
                penalty = 100.0
            else:
                penalty = 5.0

            # Scale penalty based on proximity: closer routes get higher penalty
            proximity_factor = max(0.0, (INCIDENT_ZONE_RADIUS_M - min_dist) / INCIDENT_ZONE_RADIUS_M) if INCIDENT_ZONE_RADIUS_M > 0 else 1.0
            total_score += penalty * proximity_factor
            incidents_crossed.append({
                "incident_id": inc["id"],
                "priority": "HIGH" if is_high else "LOW",
                "road_closure": bool(is_closed),
                "proximity_meters": round(min_dist, 1),
            })

    return total_score, incidents_crossed


def _max_acceptable_clean_distance(shortest_distance_m: float) -> float:
    """Return the longest clean route that is still considered a reasonable detour."""
    extra_allowance = min(
        shortest_distance_m * (MAX_CLEAN_ROUTE_DISTANCE_RATIO - 1),
        MAX_CLEAN_ROUTE_DISTANCE_EXTRA_M,
    )
    return shortest_distance_m + extra_allowance


def _incident_counts(incidents_crossed: list[dict]) -> dict:
    """Count incident types for route selection priority."""
    high_count = sum(1 for incident in incidents_crossed if incident["priority"] == "HIGH")
    low_count = sum(1 for incident in incidents_crossed if incident["priority"] == "LOW")
    closure_count = sum(1 for incident in incidents_crossed if incident.get("road_closure"))
    return {
        "total": len(incidents_crossed),
        "high": high_count,
        "low": low_count,
        "closures": closure_count,
    }


def select_best_route(routes: list[dict], incidents: list[dict]) -> tuple[dict, list[dict]]:
    """
    Select the best route with explicit safety priority:
    1. Prefer a clean route if it is not a huge detour from the shortest route.
    2. If no acceptable clean route exists, minimize incident count.
    3. For equal incident counts, prefer fewer closures/high-priority incidents.
    4. Use distance and duration only as final tie-breakers.
    """
    shortest_distance_m = min(route["distance_m"] for route in routes)
    max_clean_distance_m = _max_acceptable_clean_distance(shortest_distance_m)
    scored_routes = []

    for route in routes:
        score, crossed = score_route(route["coordinates"], incidents)
        scored_routes.append({
            "route": route,
            "score": score,
            "incidents": crossed,
            "counts": _incident_counts(crossed),
        })

    reasonable_routes = [
        item for item in scored_routes
        if item["route"]["distance_m"] <= max_clean_distance_m
    ]
    candidate_routes = reasonable_routes or scored_routes

    clean_routes = [
        item for item in candidate_routes
        if item["counts"]["total"] == 0 and item["route"]["distance_m"] <= max_clean_distance_m
    ]
    if clean_routes:
        selected = min(
            clean_routes,
            key=lambda item: (item["route"]["distance_m"], item["route"]["duration_s"]),
        )
        return selected["route"], selected["incidents"]

    selected = min(
        candidate_routes,
        key=lambda item: (
            item["counts"]["total"],
            item["counts"]["closures"],
            item["counts"]["high"],
            item["score"],
            item["route"]["distance_m"],
            item["route"]["duration_s"],
        ),
    )
    return selected["route"], selected["incidents"]


# ─── Main Orchestrator ───────────────────────────────────────────

def find_best_route(origin_lat: float, origin_lon: float, dest_lat: float, dest_lon: float) -> dict:
    """
    Find the best driving route from origin to destination,
    avoiding or minimizing exposure to active incident zones.
    """
    # 1. Fetch active incidents
    incidents = get_active_incidents()

    # 2. Fetch route alternatives
    routes = fetch_routes(origin_lat, origin_lon, dest_lat, dest_lon)
    if not routes:
        raise RuntimeError("No routes returned from routing API")

    # 3. Choose the safest reasonable route
    best_route, best_incidents = select_best_route(routes, incidents)

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

