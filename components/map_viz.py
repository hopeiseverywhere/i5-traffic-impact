import streamlit as st
import folium
from folium.plugins import Draw
from streamlit_folium import st_folium

from util.geo_utils import (
    get_coordinates_from_normalized,
    get_approx_milepost_number,
    find_nearest_milepost_coord_directional,
    nearest_milepost_from_latlon,
    detect_mile_latlon_columns,
)


def display_unified_map(mileposts, i5_line, selected_norm, prediction_result, direction_encoded):
    """Unified map with input + prediction visualization."""

    # Detect columns
    mile_col, lat_col, lon_col = detect_mile_latlon_columns(mileposts)

    # Map center
    if selected_norm is not None:
        center_lat, center_lon = get_coordinates_from_normalized(
            mileposts, selected_norm)
    else:
        center_lat = float(mileposts[lat_col].mean())
        center_lon = float(mileposts[lon_col].mean())

    # Auto zoom
    if prediction_result is None or selected_norm is None:
        zoom = 8
    else:
        impact_radius = prediction_result.get("impact_radius_miles", 1)
        zoom = 13 if impact_radius < 2 else (12 if impact_radius < 5 else 11)

    # Create map
    m = folium.Map(location=[center_lat, center_lon],
                   zoom_start=zoom, control_scale=True)

    # I-5 line
    if i5_line is not None:
        folium.GeoJson(
            i5_line,
            name="I-5 Corridor",
            tooltip="I-5 Corridor",
        ).add_to(m)

    # Prediction overlay
    if prediction_result is not None and selected_norm is not None:

        impact_radius = prediction_result["impact_radius_miles"]
        predicted_delay = prediction_result["predicted_delay_minutes"]
        prob = prediction_result["high_impact_probability"]
        high_impact_pred = prediction_result["high_impact_prediction"]

        direction = "Northbound" if direction_encoded == 0 else "Southbound"

        color = "#ff6600" if high_impact_pred else "#33aa33"
        fill_color = "#ff8533" if high_impact_pred else "#5cd65c"

        # Mile calculations
        center_mile = get_approx_milepost_number(mileposts, selected_norm)
        sign = 1 if direction_encoded == 0 else -1
        start_mile = center_mile - sign * impact_radius
        end_mile = center_mile + sign * impact_radius

        # Direction-aware milepost snapping
        start_lat, start_lon, start_mp = find_nearest_milepost_coord_directional(
            mileposts, start_mile, direction_encoded
        )
        center_lat, center_lon, center_mp = find_nearest_milepost_coord_directional(
            mileposts, center_mile, direction_encoded
        )
        end_lat, end_lon, end_mp = find_nearest_milepost_coord_directional(
            mileposts, end_mile, direction_encoded
        )

        # Impact circle
        folium.Circle(
            location=[center_lat, center_lon],
            radius=impact_radius * 1609.34,
            color=color,
            fill=True,
            fill_color=fill_color,
            fill_opacity=min(0.15 + prob * 0.5, 0.85),
            tooltip=(
                f"<b>{direction} Impact Zone</b><br>"
                f"Predicted Delay: {predicted_delay:.1f} min<br>"
                f"Radius: ±{impact_radius:.1f} mi<br>"
                f"Mileposts: {start_mp:.1f} → {end_mp:.1f}"
            ),
        ).add_to(m)

        # ============================
        # Direction-aware icons
        # ============================
        if direction_encoded == 0:   # Northbound → two ↑
            start_icon = folium.Icon(color="blue", icon="arrow-up")
            end_icon = folium.Icon(color="blue", icon="arrow-up")
        else:                        # Southbound → two ↓
            start_icon = folium.Icon(color="blue", icon="arrow-down")
            end_icon = folium.Icon(color="blue", icon="arrow-down")

        center_icon = folium.Icon(color="red", icon="info-sign")

        # ============================
        # Markers
        # ============================
        folium.Marker(
            [start_lat, start_lon],
            icon=start_icon,
            tooltip=f"Start MP {start_mp:.1f}",
        ).add_to(m)

        folium.Marker(
            [center_lat, center_lon],
            icon=center_icon,
            tooltip=f"Incident MP {center_mp:.1f}",
        ).add_to(m)

        folium.Marker(
            [end_lat, end_lon],
            icon=end_icon,
            tooltip=f"End MP {end_mp:.1f}",
        ).add_to(m)

    # Drawing tool
    Draw(
        draw_options={"polyline": False, "polygon": False, "rectangle": False,
                      "circle": False, "circlemarker": False, "marker": True},
        edit_options={}
    ).add_to(m)

    # Render big map
    output = st_folium(
        m,
        width="100%",
        height=750,
        returned_objects=["last_active_drawing", "all_drawings"],
    )
    
    

    # Snap user click
    if output:
        feature = output.get("last_active_drawing")
        if not feature:
            drawings = output.get("all_drawings") or []
            if drawings:
                feature = drawings[-1]

        if feature and feature["geometry"]["type"] == "Point":
            lon, lat = feature["geometry"]["coordinates"]

            norm_pos, approx_mile, snap_lat, snap_lon = nearest_milepost_from_latlon(
                mileposts, lat, lon, direction_encoded
            )

            st.session_state["selected_norm"] = norm_pos
            st.session_state["approx_mile"] = approx_mile

            st.caption(
                f"📍 Snapped to I-5 MP ≈ {approx_mile:.1f} (normalized {norm_pos:.3f})"
            )
