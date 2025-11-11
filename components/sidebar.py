import streamlit as st
from util.geo_utils import get_approx_milepost_number
from util.sidebar_config import INCIDENT_TYPES, LANE_CLOSURES, DIRECTIONS, DEFAULTS


def prediction_sidebar(mileposts):
    """Sidebar form for user input. Returns (params, submitted flag)."""

    st.sidebar.header("Predict Traffic Incident Impact")

    # ------------------------------
    # Time features
    # ------------------------------
    hour = st.sidebar.slider("Hour of Day", 0, 23, DEFAULTS["hour"])
    day_of_week = st.sidebar.slider("Day of Week", 0, 6, DEFAULTS["day_of_week"], help="0=Mon, 6=Sun")

    is_rush_hour = int(7 <= hour <= 10 or 16 <= hour <= 19)
    is_weekend = int(day_of_week >= 5)

    rush_desc = "✅ Rush Hour" if is_rush_hour else "Off-Peak"
    weekend_desc = "Weekend" if is_weekend else "Weekday"
    st.sidebar.caption(f"{rush_desc} · {weekend_desc}")

    # ------------------------------
    # Location features
    # ------------------------------
    location_zone = st.sidebar.slider("Location Zone", 0, 9, DEFAULTS["location_zone"])
    milepost_normalized = st.sidebar.slider("Milepost (0–1 normalized)", 0.0, 1.0, DEFAULTS["milepost_normalized"])

    try:
        approx_mile = get_approx_milepost_number(mileposts, milepost_normalized)
        st.sidebar.caption(f"📍 Approx. Milepost: **{approx_mile:.1f}**")
    except Exception as e:
        st.sidebar.caption(f"⚠️ Unable to estimate milepost ({e})")

    # ------------------------------
    # Incident characteristics
    # ------------------------------
    incident_label = st.sidebar.selectbox(
        "Incident Type",
        options=list(INCIDENT_TYPES.keys()),
        format_func=lambda x: f"{x} – {INCIDENT_TYPES[x]}",
        index=DEFAULTS["incident_index"],
    )
    lane_label = st.sidebar.selectbox(
        "Lane Closure",
        options=list(LANE_CLOSURES.keys()),
        format_func=lambda x: f"{x} – {LANE_CLOSURES[x]}",
        index=DEFAULTS["lane_index"],
    )
    direction_encoded = st.sidebar.selectbox(
        "Direction Encoded",
        options=list(DIRECTIONS.keys()),
        format_func=lambda x: DIRECTIONS[x],
        index=DEFAULTS["direction_index"],
    )

    blocking_encoded = st.sidebar.selectbox("Blocking (0 = No, 1 = Yes)", [0, 1], index=DEFAULTS["blocking_index"])
    severity_score = st.sidebar.slider("Severity Score (1–3)", 1, 3, DEFAULTS["severity_default"])

    rush_blocking_interaction = int(is_rush_hour and blocking_encoded == 1)
    submitted = st.sidebar.button("🚗 Predict Impact")

    params = {
        "hour": hour,
        "day_of_week": day_of_week,
        "is_rush_hour": is_rush_hour,
        "is_weekend": is_weekend,
        "location_zone": location_zone,
        "milepost_normalized": milepost_normalized,
        "incident_type_encoded": incident_label,
        "lane_closure_encoded": lane_label,
        "direction_encoded": direction_encoded,
        "blocking_encoded": blocking_encoded,
        "severity_score": severity_score,
        "rush_blocking_interaction": rush_blocking_interaction,
    }

    return params, submitted
