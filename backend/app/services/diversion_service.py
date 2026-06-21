"""
Diversion Service — Generates Folium maps for incident visualization.

Shows:
    - Incident location marker
    - Impact radius circle
    - Nearby context via OpenStreetMap tiles
    - Suggested diversion awareness zone

No route optimization — just visual context for quick decision-making.
"""

import folium
from app.config import MAPS_DIR
from app.utils.mappings import CORRIDOR, EVENT_TYPE
from app.services.location_service import _get_mappls_token


def generate_diversion_map(
    latitude: float,
    longitude: float,
    incident_id: str = None,
    corridor: int = None,
    event_type: int = None,
    priority_label: str = None,
    risk_level: str = None,
) -> str:
    """
    Generate a map HTML string for the incident location.
    Uses MapmyIndia (Mappls) Web SDK if credentials are valid, otherwise
    falls back to OpenStreetMap via Folium.

    Args:
        latitude: Incident latitude
        longitude: Incident longitude
        incident_id: Optional incident ID for the title
        corridor: Optional corridor code for labeling
        event_type: Optional event type for labeling
        priority_label: Optional priority label (HIGH/LOW)
        risk_level: Optional risk level

    Returns:
        HTML string of the generated map
    """
    # 1. Attempt to get MapmyIndia/Mappls static API Key or OAuth token
    from app.config import MAPMYINDIA_API_KEY
    map_key = MAPMYINDIA_API_KEY or _get_mappls_token()

    if map_key:

        # Build popup content for MapmyIndia
        popup_lines = [f"<b>Incident: {incident_id or 'N/A'}</b>"]
        if corridor is not None:
            popup_lines.append(f"Corridor: {CORRIDOR.get(corridor, corridor)}")
        if event_type is not None:
            popup_lines.append(f"Type: {EVENT_TYPE.get(event_type, event_type)}")
        if priority_label:
            popup_lines.append(f"Priority: {priority_label}")
        if risk_level:
            popup_lines.append(f"Risk: {risk_level}")
        popup_lines.append(f"Location: {latitude:.5f}, {longitude:.5f}")
        popup_html = "<br>".join(popup_lines)

        # Determine correct JS SDK URL based on auth type
        if MAPMYINDIA_API_KEY:
            sdk_url = f"https://sdk.mappls.com/map/sdk/web?v=3.0&access_token={map_key}"
        else:
            sdk_url = f"https://apis.mappls.com/advancedmaps/v1/{map_key}/map_sdk?v=3.0&layer=vector"

        # Generate HTML using MapmyIndia Web SDK v3.0
        html_content = f"""<!DOCTYPE html>
<html>
<head>
    <title>ARES MapmyIndia Map - {incident_id or 'Incident'}</title>
    <meta name="viewport" content="initial-scale=1.0, user-scalable=no" />
    <style>
        html, body, #map {{ margin: 0; padding: 0; width: 100%; height: 100%; }}
        .mappls-popup-content {{ font-family: sans-serif; font-size: 13px; line-height: 1.4; }}
    </style>
    <script src="{sdk_url}"></script>
</head>

<body>
    <div id="map"></div>
    <script>
        var map = new mappls.Map('map', {{
            center: [{latitude}, {longitude}],
            zoom: 16
        }});

        map.addListener('load', function() {{
            // 1. Incident Marker
            var marker = new mappls.Marker({{
                map: map,
                position: {{ lat: {latitude}, lng: {longitude} }},
                fitbounds: false,
                popupHtml: '<div class="mappls-popup-content">{popup_html}</div>'
            }});

            // 2. Impact Zone (200m red circle)
            new mappls.Circle({{
                map: map,
                center: {{ lat: {latitude}, lng: {longitude} }},
                radius: 200,
                fillColor: '#FF0000',
                fillOpacity: 0.15,
                strokeColor: '#FF0000',
                strokeOpacity: 0.8,
                strokeWeight: 2
            }});

            // 3. Diversion Awareness Zone (500m orange circle)
            new mappls.Circle({{
                map: map,
                center: {{ lat: {latitude}, lng: {longitude} }},
                radius: 500,
                fillColor: '#FFA500',
                fillOpacity: 0.08,
                strokeColor: '#FFA500',
                strokeOpacity: 0.8,
                strokeWeight: 2
            }});

            // 4. Extended Impact Area (1km blue circle)
            new mappls.Circle({{
                map: map,
                center: {{ lat: {latitude}, lng: {longitude} }},
                radius: 1000,
                fillColor: '#0000FF',
                fillOpacity: 0.0,
                strokeColor: '#0000FF',
                strokeOpacity: 0.5,
                strokeWeight: 1
            }});

            // 5. Direction Markers
            var offsets = [
                [0.003, 0, 'N'],
                [-0.003, 0, 'S'],
                [0, 0.003, 'E'],
                [0, -0.003, 'W']
            ];
            offsets.forEach(function(off) {{
                new mappls.Marker({{
                    map: map,
                    position: {{ lat: {latitude} + off[0], lng: {longitude} + off[1] }},
                    html: '<div style="font-family: sans-serif; font-size: 11px; font-weight: bold; color: #555; background: rgba(255,255,255,0.8); padding: 2px 5px; border: 1px solid #ccc; border-radius: 3px;">' + off[2] + '</div>'
                }});
            }});
        }});
    </script>
</body>
</html>"""

        if incident_id:
            filepath = MAPS_DIR / f"{incident_id}.html"
            with open(filepath, "w", encoding="utf-8") as f:
                f.write(html_content)

        return html_content

    # 2. Fallback to OpenStreetMap via Folium
    print("[INFO] MapmyIndia credentials not configured. Falling back to Folium OpenStreetMap.")
    m = folium.Map(
        location=[latitude, longitude],
        zoom_start=16,
        tiles="OpenStreetMap",
    )

    popup_lines = [f"<b>Incident: {incident_id or 'N/A'}</b>"]
    if corridor is not None:
        popup_lines.append(f"Corridor: {CORRIDOR.get(corridor, corridor)}")
    if event_type is not None:
        popup_lines.append(f"Type: {EVENT_TYPE.get(event_type, event_type)}")
    if priority_label:
        popup_lines.append(f"Priority: {priority_label}")
    if risk_level:
        popup_lines.append(f"Risk: {risk_level}")
    popup_lines.append(f"Location: {latitude:.5f}, {longitude:.5f}")

    popup_html = "<br>".join(popup_lines)

    folium.Marker(
        location=[latitude, longitude],
        popup=folium.Popup(popup_html, max_width=300),
        tooltip="Incident Location (OSM Fallback)",
        icon=folium.Icon(color="red", icon="exclamation-triangle", prefix="fa"),
    ).add_to(m)

    folium.Circle(
        location=[latitude, longitude],
        radius=200,
        color="red",
        fill=True,
        fill_color="red",
        fill_opacity=0.2,
        popup="Impact Zone (200m)",
    ).add_to(m)

    folium.Circle(
        location=[latitude, longitude],
        radius=500,
        color="orange",
        fill=True,
        fill_color="orange",
        fill_opacity=0.1,
        popup="Diversion Awareness Zone (500m)",
        dash_array="10",
    ).add_to(m)

    folium.Circle(
        location=[latitude, longitude],
        radius=1000,
        color="blue",
        fill=False,
        dash_array="5",
        popup="Extended Impact Area (1km)",
    ).add_to(m)

    offsets = [
        (0.003, 0, "N", "↑ North"),
        (-0.003, 0, "S", "↓ South"),
        (0, 0.003, "E", "→ East"),
        (0, -0.003, "W", "← West"),
    ]
    for lat_off, lon_off, label, tooltip_text in offsets:
        folium.Marker(
            location=[latitude + lat_off, longitude + lon_off],
            tooltip=tooltip_text,
            icon=folium.DivIcon(
                html=f'<div style="font-size:12px;font-weight:bold;color:#333;">{label}</div>',
                icon_size=(20, 20),
            ),
        ).add_to(m)

    if incident_id:
        filepath = MAPS_DIR / f"{incident_id}.html"
        m.save(str(filepath))

    return m._repr_html_()

