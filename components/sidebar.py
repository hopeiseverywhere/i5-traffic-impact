import streamlit as st
from util.sidebar_config import INCIDENT_TYPES, LANE_CLOSURES, DIRECTIONS, DEFAULTS


def prediction_sidebar(selected_milepost_normalized, approx_mile):
    """
    Sidebar form for prediction inputs.
    Takes:
        selected_milepost_normalized : float or None  (map click)
        approx_mile                  : float or None  (human milepost)
    Returns:
        params dict, submitted flag
    """

    st.sidebar.header("Predict Traffic Incident Impact")

    # ===============================
    # RESET BUTTON (optional)
    # ===============================
    if st.sidebar.button("🔄 Reset All"):
        for key in list(st.session_state.keys()):
            del st.session_state[key]
        st.rerun()

    # ===============================
    # TIME FEATURES
    # ===============================
    hour = st.sidebar.slider(
        "Hour of Day", 0, 23, DEFAULTS["hour"]
    )
    day_of_week = st.sidebar.slider(
        "Day of Week",
        0, 6,
        DEFAULTS["day_of_week"],
        help="0=Mon, 6=Sun"
    )

    is_weekend = int(day_of_week >= 5)
    is_rush_hour = int(
        (not is_weekend)
        and (7 <= hour <= 10 or 16 <= hour <= 19)
    )

    st.sidebar.caption(
        f"{'🚗 Rush Hour' if is_rush_hour else 'Off-Peak'} · "
        f"{'Weekend' if is_weekend else 'Weekday'}"
    )

    # ===============================
    # LOCATION FEATURES (MAP)
    # ===============================
    location_zone = st.sidebar.slider(
        "Location Zone", 0, 9, DEFAULTS["location_zone"]
    )

    if selected_milepost_normalized is not None and approx_mile is not None:
        milepost_normalized = float(selected_milepost_normalized)
        st.sidebar.caption(
            f"📍 Map Milepost: **{approx_mile:.1f}** "
            f"(normalized = {milepost_normalized:.3f})"
        )
    else:
        milepost_normalized = DEFAULTS["milepost_normalized"]
        st.sidebar.caption(
            f"📍 No map location selected — using default "
            f"(normalized = {milepost_normalized:.3f})"
        )

    # ===============================
    # INCIDENT CHARACTERISTICS
    # ===============================
    incident_label = st.sidebar.selectbox(
        "Incident Type",
        options=list(INCIDENT_TYPES.keys()),
        format_func=lambda k: f"{k} – {INCIDENT_TYPES[k]}",
        index=DEFAULTS["incident_index"],
    )

    lane_label = st.sidebar.selectbox(
        "Lane Closure",
        options=list(LANE_CLOSURES.keys()),
        format_func=lambda k: f"{k} – {LANE_CLOSURES[k]}",
        index=DEFAULTS["lane_index"],
    )

    direction_encoded = st.sidebar.selectbox(
        "Direction",
        options=list(DIRECTIONS.keys()),
        format_func=lambda k: DIRECTIONS[k],
        index=DEFAULTS["direction_index"],
    )

    blocking_encoded = st.sidebar.selectbox(
        "Blocking (0 = No, 1 = Yes)",
        [0, 1],
        index=DEFAULTS["blocking_index"],
    )

    severity_score = st.sidebar.slider(
        "Severity Score (1–3)",
        1, 3, DEFAULTS["severity_default"]
    )

    rush_blocking_interaction = int(is_rush_hour and blocking_encoded == 1)

    # ===============================
    # SUBMIT BUTTON
    # ===============================
    submitted = st.sidebar.button("🔮 Predict Impact")

    # ===============================
    # PACK FEATURES INTO PARAMS
    # ===============================
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
