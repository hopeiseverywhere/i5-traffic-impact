import streamlit as st
import pydeck as pdk
from util.map_layers import make_path_layer
from util.geo_utils import (
    get_coordinates_from_normalized,
    get_approx_milepost_number,
    find_nearest_milepost_coord,
)
from util.map_config import MAP_STYLE, COLORS, TOOLTIP_STYLE, DEFAULT_ZOOM, DEFAULT_HEIGHT


def display_prediction_map(result, mileposts, i5_line, normalized, direction_encoded):
    """Display predicted impact zone on map."""

    # Extract key info
    lat, lon = get_coordinates_from_normalized(mileposts, normalized)
    impact_radius = result.get("impact_radius_miles", 0)
    predicted_delay = result.get("predicted_delay_minutes", 0)
    confidence = result.get("confidence", "Unknown")
    direction = "Northbound" if direction_encoded == 0 else "Southbound"

    # Color based on Traffic Impact Severity
    high_impact_pred = result.get("high_impact_prediction", 0)
    prob = float(result.get("high_impact_probability", 0.0))

    if high_impact_pred:  # predicted severe impact
        r = int(255)
        g = int(165 - (prob * 80))
        b = int(0)
    else:  # predicted low / no severe impact
        r = int(0 + prob * 255)
        g = int(128 + prob * 127)
        b = int(0)

    # transparency (alpha) scales smoothly with probability (0.0–1.0)
    alpha = int(60 + prob * 120)  # 60–180 range

    circle_color = [r, g, b, alpha]

    color_start = COLORS["dot_start_nb"] if direction_encoded == 0 else COLORS["dot_start_sb"]
    color_center = COLORS["dot_center"]
    color_end = COLORS["dot_end"]

    # Compute mileposts
    center_mile = get_approx_milepost_number(mileposts, normalized)
    sign = 1 if direction_encoded == 0 else -1
    start_mile = center_mile - sign * impact_radius
    end_mile = center_mile + sign * impact_radius

    start_lat, start_lon, start_mp = find_nearest_milepost_coord(
        mileposts, start_mile)
    center_lat, center_lon, center_mp = find_nearest_milepost_coord(
        mileposts, center_mile)
    end_lat, end_lon, end_mp = find_nearest_milepost_coord(mileposts, end_mile)

    # Layers
    path_layer = make_path_layer(i5_line)
    circle_layer = pdk.Layer(
        "ScatterplotLayer",
        data=[{"lat": lat, "lon": lon}],
        get_position='[lon, lat]',
        get_radius=impact_radius * 1609.34,
        get_fill_color=circle_color,
        pickable=True,
    )
    dot_data = [
        {"lat": start_lat, "lon": start_lon,
            "label": f"Start MP {start_mp:.1f}", "color": color_start},
        {"lat": center_lat, "lon": center_lon,
            "label": f"Incident MP {center_mp:.1f}", "color": color_center},
        {"lat": end_lat, "lon": end_lon,
            "label": f"End MP {end_mp:.1f}", "color": color_end},
    ]
    dot_layer = pdk.Layer("ScatterplotLayer", data=dot_data,
                          get_position='[lon, lat]', get_color='color', get_radius=100)
    label_layer = pdk.Layer("TextLayer", data=dot_data,
                            get_position='[lon, lat]', get_text='label', get_size=12, get_color=COLORS["label_text"])

    # Deck
    view_state = pdk.ViewState(
        latitude=center_lat, longitude=center_lon, zoom=DEFAULT_ZOOM)
    deck = pdk.Deck(
        map_style=MAP_STYLE,
        initial_view_state=view_state,
        layers=[path_layer, circle_layer, dot_layer, label_layer],
        tooltip={
            "html": (
                f"<b>{direction} Impact Zone</b><br>"
                f"Predicted Delay: {predicted_delay:.1f} min<br>"
                f"Impact Radius: ±{impact_radius:.1f} mi<br>"
                f"Mileposts: {start_mp:.1f} → {end_mp:.1f}"
            ),
            "style": TOOLTIP_STYLE,
        },
    )

    st.pydeck_chart(deck, use_container_width=True, height=DEFAULT_HEIGHT)

    st.caption(
        f"{direction} predicted impact spans from MP {start_mp:.1f} to MP {end_mp:.1f} "
        f"(centered at MP {center_mp:.1f}, ±{impact_radius:.1f} mi, predicted delay {predicted_delay:.1f} min)."
    )
