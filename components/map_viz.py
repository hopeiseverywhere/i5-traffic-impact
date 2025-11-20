import streamlit as st
import folium
from folium.plugins import Draw
from streamlit_folium import st_folium

from util.map_config import (
    DEFAULT_ZOOM,
    IMPACT_ZOOM_LEVELS,
    MILES_TO_METERS,
    HIGH_IMPACT_COLOR_EDGE,
    HIGH_IMPACT_COLOR_FILL,
    LOW_IMPACT_COLOR_EDGE,
    LOW_IMPACT_COLOR_FILL,
    DIRECTION_ICONS,
    DRAW_OPTIONS,
    EDIT_OPTIONS,
)

from util.geo_utils import (
    get_coordinates_from_normalized,
    get_approx_milepost_number,
    nearest_milepost_from_latlon,
    find_nearest_milepost_coord_directional,
    detect_mile_latlon_columns,
)
from util.segments import TRIP_SEGMENTS, SEGMENT_POINTS

# ==================================================================
#                   MAIN MAP RENDERING FUNCTION
# ==================================================================
def display_unified_map(
    mileposts,
    selected_norm,
    prediction_result,
    direction_encoded,
    all_trips=None,           # list of all 8 trips
    selected_trip_id=None,    # selected trip ID
):
    """Unified map showing 8 trips as layers, only selected trip visible."""

    # Detect needed columns
    mile_col, lat_col, lon_col = detect_mile_latlon_columns(mileposts)

    # =============================================================
    #                   MAP CENTER LOGIC
    # =============================================================
    if selected_trip_id is not None and all_trips is not None:
        # center on midpoint of selected trip
        trip = next(t for t in all_trips if t["properties"]["TripId"] == selected_trip_id)
        coords = trip["geometry"]["coordinates"]
        mid = len(coords) // 2
        center_lon, center_lat = coords[mid]
    else:
        # map starts blank on Seattle region
        center_lat, center_lon = 47.60, -122.33
        selected_norm = None

    # =============================================================
    #                         ZOOM LEVEL
    # =============================================================
    if prediction_result is None:
        zoom = DEFAULT_ZOOM
    else:
        r = prediction_result["impact_radius_miles"]
        zoom = (
            IMPACT_ZOOM_LEVELS["small"] if r < 2 else
            IMPACT_ZOOM_LEVELS["medium"] if r < 5 else
            IMPACT_ZOOM_LEVELS["large"]
        )

    # Create map
    m = folium.Map(
        location=[center_lat, center_lon],
        zoom_start=zoom,
        control_scale=True,
    )

    # =============================================================
    #           DISPLAY 8 TRIPS AS 8 LAYERS (ONLY ONE VISIBLE)
    # =============================================================
    if all_trips is not None:
        for trip in all_trips:
            tid = trip["properties"]["TripId"]
            direction = trip["properties"]["Direction"]

            visible = tid == selected_trip_id

            # Get HOV flag
            hov = next(t for t in TRIP_SEGMENTS if t["Id"] == tid)["UsesHOV"]

            # Colors: GP = blue, HOV = green
            base_color = "#1d6ef2"      # blue (non-HOV)
            if hov:
                base_color = "#43a560"  # green (HOV)

            # Selected trip gets a brighter highlight
            highlight_color = base_color

            folium.GeoJson(
                trip,
                name=f"Trip {tid} – {direction}",
                show=True,  # always show, but dim non-selected ones
                tooltip=(
                    f"Trip {tid} – {direction}<br>"
                    f"{'HOV Lane' if hov else 'General Purpose'}"
                ),
                style_function=lambda f, v=visible, bc=base_color, hc=highlight_color: {
                    "color": hc if v else bc,
                    "weight": 7 if v else 3,
                    "opacity": 1.0 if v else 0.35,
                },
            ).add_to(m)

        # Allow toggling layers
        folium.LayerControl().add_to(m)

    # =============================================================
    #                DRAW PREDICTION OVERLAY (if any)
    # =============================================================
    if prediction_result is not None:

        impact_radius = prediction_result["impact_radius_miles"]
        predicted_delay = prediction_result["predicted_delay_minutes"]
        prob = prediction_result["high_impact_probability"]
        high = prediction_result["high_impact_prediction"]

        direction_info = DIRECTION_ICONS[direction_encoded]
        edge_color = HIGH_IMPACT_COLOR_EDGE if high else LOW_IMPACT_COLOR_EDGE
        fill_color = HIGH_IMPACT_COLOR_FILL if high else LOW_IMPACT_COLOR_FILL

        # ---- snapped center ----
        approx_mile = st.session_state.get("approx_mile")
        snap_center_lat = st.session_state.get("snap_lat")
        snap_center_lon = st.session_state.get("snap_lon")

        if approx_mile is None or snap_center_lat is None:
            if selected_norm is None:
                selected_norm = 0.5

            approx_mile = get_approx_milepost_number(mileposts, selected_norm)
            snap_center_lat, snap_center_lon = get_coordinates_from_normalized(
                mileposts, selected_norm
            )

            st.session_state["approx_mile"] = approx_mile
            st.session_state["snap_lat"] = snap_center_lat
            st.session_state["snap_lon"] = snap_center_lon

        # ---- compute start/end miles ----
        sign = 1 if direction_encoded == 0 else -1
        start_mile = approx_mile - sign * impact_radius
        end_mile = approx_mile + sign * impact_radius

        mp_start_lat, mp_start_lon, _ = find_nearest_milepost_coord_directional(
            mileposts, start_mile, direction_encoded
        )
        mp_end_lat, mp_end_lon, _ = find_nearest_milepost_coord_directional(
            mileposts, end_mile, direction_encoded
        )

        start_lat, start_lon = mp_start_lat, mp_start_lon
        end_lat, end_lon = mp_end_lat, mp_end_lon

        # ---- impact circle ----
        folium.Circle(
            location=[snap_center_lat, snap_center_lon],
            radius=impact_radius * MILES_TO_METERS,
            color=edge_color,
            fill=True,
            fill_color=fill_color,
            fill_opacity=min(0.15 + prob * 0.5, 0.85),
            tooltip=(
                f"<b>{direction_info['label']} Impact Zone</b><br>"
                f"Predicted Delay: {predicted_delay:.1f} min<br>"
                f"Radius: ±{impact_radius:.1f} mi"
            ),
        ).add_to(m)

        # Start marker
        start_icon_color, start_icon_symbol = direction_info["start"]
        folium.Marker(
            [start_lat, start_lon],
            icon=folium.Icon(color=start_icon_color, icon=start_icon_symbol),
            tooltip=f"Start ~MP {start_mile:.1f}",
        ).add_to(m)

        # Center marker
        folium.Marker(
            [snap_center_lat, snap_center_lon],
            icon=folium.Icon(color="red", icon="info-sign"),
            tooltip=(
                f"<b>Incident Center</b><br>"
                f"MP ≈ {approx_mile:.2f}<br>"
                f"Lat: {snap_center_lat:.6f}<br>"
                f"Lon: {snap_center_lon:.6f}"
            ),
        ).add_to(m)

        # End marker
        end_icon_color, end_icon_symbol = direction_info["end"]
        folium.Marker(
            [end_lat, end_lon],
            icon=folium.Icon(color=end_icon_color, icon=end_icon_symbol),
            tooltip=f"End ~MP {end_mile:.1f}",
        ).add_to(m)

    # =============================================================
    #                      DRAWING TOOL
    # =============================================================
    Draw(draw_options=DRAW_OPTIONS, edit_options=EDIT_OPTIONS).add_to(m)

    # =============================================================
    #                      PROCESS MAP CLICKS
    # =============================================================
    output = st_folium(
        m,
        width="100%",
        height=750,
        returned_objects=["last_active_drawing", "all_drawings"],
    )

    if output:
        feature = output.get("last_active_drawing")
        if not feature:
            drawings = output.get("all_drawings") or []
            if drawings:
                feature = drawings[-1]

        if feature and feature["geometry"]["type"] == "Point":
            lon, lat = feature["geometry"]["coordinates"]

            # =====================================================
            #       SNAP TO SELECTED TRIP (Shapely)
            # =====================================================
            if selected_trip_id is not None and all_trips is not None:
                import shapely.geometry as geom

                # find selected trip geometry
                trip = next(t for t in all_trips if t["properties"]["TripId"] == selected_trip_id)
                coords = trip["geometry"]["coordinates"]   # [[lon, lat], [lon, lat], ...]

                line = geom.LineString(coords)
                clicked = geom.Point(lon, lat)

                # project → interpolate = nearest point on polyline
                snapped_point = line.interpolate(line.project(clicked))

                snap_lon, snap_lat = snapped_point.x, snapped_point.y

            else:
                # fallback: no snapping, raw click
                snap_lat, snap_lon = lat, lon

            # save snapped
            st.session_state["snap_lat"] = snap_lat
            st.session_state["snap_lon"] = snap_lon

            # convert to milepost
            norm_pos, approx_mile, _, _ = nearest_milepost_from_latlon(
                mileposts, snap_lat, snap_lon, direction_encoded
            )

            st.session_state["selected_norm"] = norm_pos
            st.session_state["approx_mile"] = approx_mile

            st.caption(
                f"📍 Snapped to Trip {selected_trip_id} at MP ≈ {approx_mile:.1f} "
                f"(lat {snap_lat:.6f}, lon {snap_lon:.6f})"
            )
            st.session_state["pending_map_rerun"] = True
