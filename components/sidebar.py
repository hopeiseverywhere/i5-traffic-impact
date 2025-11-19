import streamlit as st
from util.sidebar_config import INCIDENT_TYPES, LANE_CLOSURES, DIRECTIONS, DEFAULTS


def prediction_sidebar(selected_milepost_normalized, approx_mile):
    """
    Sidebar form for prediction inputs.

    Now uses ONLY map-selected milepost (no location_zone).
    """

    st.sidebar.header("Predict Traffic Incident Impact")

    # -------------------------------------------
    # TIME FEATURES
    # -------------------------------------------
    hour = st.sidebar.slider("Hour of Day", 0, 23, DEFAULTS["hour"])
    day_of_week = st.sidebar.slider(
        "Day of Week", 0, 6, DEFAULTS["day_of_week"], help="0=Mon · 6=Sun"
    )

    is_weekend = int(day_of_week >= 5)
    is_rush_hour = int(
        (not is_weekend) and (7 <= hour <= 10 or 16 <= hour <= 19)
    )

    st.sidebar.caption(
        f"{'🚦 Rush Hour' if is_rush_hour else 'Off-Peak'} · "
        f"{'Weekend' if is_weekend else 'Weekday'}"
    )

    # -------------------------------------------
    # MILEPOST FROM MAP
    # -------------------------------------------
    if selected_milepost_normalized is not None and approx_mile is not None:
        milepost_normalized = float(selected_milepost_normalized)
        st.sidebar.success(
            f"📍 Map Milepost Selected → **{approx_mile:.1f}** "
            f"(normalized {milepost_normalized:.3f})"
        )
    else:
        milepost_normalized = DEFAULTS["milepost_normalized"]
        st.sidebar.warning(
            "📍 Click on the map to choose a milepost."
        )

    # -------------------------------------------
    # INCIDENT ATTRIBUTES
    # -------------------------------------------
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
        "Blocking (0=No, 1=Yes)",
        [0, 1],
        index=DEFAULTS["blocking_index"],
    )

    severity_score = st.sidebar.slider(
        "Severity Score (1–3)",
        1, 3, DEFAULTS["severity_default"],
    )

    rush_blocking_interaction = int(is_rush_hour and blocking_encoded == 1)

    # -------------------------------------------
    # SUBMIT
    # -------------------------------------------
    submitted = st.sidebar.button("🚗 Predict Impact")

    # -------------------------------------------
    # PACK FEATURES
    # -------------------------------------------
    params = {
        "hour": hour,
        "day_of_week": day_of_week,
        "is_rush_hour": is_rush_hour,
        "is_weekend": is_weekend,

        # only using map-selected milepost now
        "milepost_normalized": milepost_normalized,

        # Encoded labels
        "incident_type_encoded": incident_label,
        "lane_closure_encoded": lane_label,
        "direction_encoded": direction_encoded,
        "blocking_encoded": blocking_encoded,

        "severity_score": severity_score,
        "rush_blocking_interaction": rush_blocking_interaction,
    }

    return params, submitted
