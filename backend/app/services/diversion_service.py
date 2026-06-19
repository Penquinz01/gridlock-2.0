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
    Generate a Folium map HTML string for the incident location.

    Args:
        latitude: Incident latitude
        longitude: Incident longitude
        incident_id: Optional incident ID for the title
        corridor: Optional corridor code for labeling
        event_type: Optional event type for labeling
        priority_label: Optional priority label (HIGH/LOW)
        risk_level: Optional risk level

    Returns:
        HTML string of the generated Folium map
    """
    # Create map centered on incident
    m = folium.Map(
        location=[latitude, longitude],
        zoom_start=16,
        tiles="OpenStreetMap",
    )

    # Build popup content
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

    # Incident marker (red)
    folium.Marker(
        location=[latitude, longitude],
        popup=folium.Popup(popup_html, max_width=300),
        tooltip="Incident Location",
        icon=folium.Icon(color="red", icon="exclamation-triangle", prefix="fa"),
    ).add_to(m)

    # Impact zone — inner circle (immediate area)
    folium.Circle(
        location=[latitude, longitude],
        radius=200,  # 200 meters
        color="red",
        fill=True,
        fill_color="red",
        fill_opacity=0.2,
        popup="Impact Zone (200m)",
    ).add_to(m)

    # Awareness zone — outer circle (diversion awareness)
    folium.Circle(
        location=[latitude, longitude],
        radius=500,  # 500 meters
        color="orange",
        fill=True,
        fill_color="orange",
        fill_opacity=0.1,
        popup="Diversion Awareness Zone (500m)",
        dash_array="10",
    ).add_to(m)

    # Wider context zone
    folium.Circle(
        location=[latitude, longitude],
        radius=1000,  # 1 km
        color="blue",
        fill=False,
        dash_array="5",
        popup="Extended Impact Area (1km)",
    ).add_to(m)

    # Cardinal direction markers for orientation
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

    # Save to file if incident_id provided
    if incident_id:
        filepath = MAPS_DIR / f"{incident_id}.html"
        m.save(str(filepath))

    return m._repr_html_()
