import streamlit as st
from util.sidebar_config import INCIDENT_TYPES, LANE_CLOSURES, DIRECTIONS, DEFAULTS
from util.data_loader import load_trip_segments, get_trip_by_id
from util.segments import TRIP_SEGMENTS, SEGMENT_POINTS

TRIP_MAP = {(t["Start"], t["End"]): t["Id"] for t in TRIP_SEGMENTS}

START_TO_END = {}
for t in TRIP_SEGMENTS:
    START_TO_END.setdefault(t["Start"], set()).add(t["End"])


def prediction_sidebar(selected_norm, approx_mile):

    st.sidebar.header("Predict Traffic Incident Impact")

    # ------------------------------------------------
    # Reset Button
    # ------------------------------------------------
    if st.sidebar.button("🔄 Reset All"):
        st.session_state.clear()
        st.rerun()

    # ======================================================
    # 1 SELECT START 
    # ======================================================
    start_options = sorted(START_TO_END.keys())
    selected_start = st.sidebar.selectbox(
        "1️⃣ Select Start Location",
        start_options,
        format_func=lambda sid: SEGMENT_POINTS[sid]["Name"],
        key="start_selectbox",
    )

    # ======================================================
    # 2 SELECT END 
    # ======================================================
    end_options = sorted(START_TO_END[selected_start])
    selected_end = st.sidebar.selectbox(
        "2️⃣ Select Destination",
        end_options,
        format_func=lambda eid: SEGMENT_POINTS[eid]["Name"],
        key="end_selectbox",
    )

    # ======================================================
    # CONFIRM BUTTON
    # ======================================================
    if st.sidebar.button("✔️ Confirm Trip Selection"):
        trip_id = TRIP_MAP[(selected_start, selected_end)]
        st.session_state["selected_trip_id"] = trip_id

        # Clear old click + old predictions
        st.session_state["approx_mile"] = None
        st.session_state["selected_norm"] = None
        st.session_state["prediction_result"] = None
        
    # ======================================================
    # If trip not confirmed yet → stop here
    # ======================================================
    if st.session_state.get("selected_trip_id") is None:
        st.sidebar.info("➡️ Choose a start & end point, then click **Confirm Trip Selection**.")
        return None, False

    # Load selected trip data
    trips = load_trip_segments("./geodata/i5_trip_segments.geojson")
    selected_trip = get_trip_by_id(trips, st.session_state["selected_trip_id"])

    # Metadata
    t = next(t for t in TRIP_SEGMENTS if t["Id"] == st.session_state["selected_trip_id"])
    start_info = SEGMENT_POINTS[t["Start"]]
    end_info = SEGMENT_POINTS[t["End"]]
    hov_label = "HOV Lane" if t["UsesHOV"] else "General Purpose"

    st.sidebar.success(
        f"🛣 **Trip {t['Id']}**\n"
        f"- **Start:** {start_info['Name']} (MP {start_info['Milepost']:.2f})\n"
        f"- **End:** {end_info['Name']} (MP {end_info['Milepost']:.2f})\n"
        f"- **Direction:** {selected_trip['properties']['Direction']}\n"
        f"- **Lane Type:** {hov_label}"
    )

    # ======================================================
    # WAIT FOR MAP CLICK
    # ======================================================
    if approx_mile is None:
        st.sidebar.warning("📍 Click on the map to place the incident.")
        return None, False

    st.sidebar.info(f"📍 Incident at MP {approx_mile:.2f}")

    # ============================
    # FULL FEATURE SET
    # ============================
    hour = st.sidebar.slider("Hour", 0, 23, DEFAULTS["hour"])
    day_of_week = st.sidebar.slider("Day of Week", 0, 6, DEFAULTS["day_of_week"])

    is_weekend = int(day_of_week >= 5)
    is_rush_hour = int((not is_weekend) and (7 <= hour <= 10 or 16 <= hour <= 19))

    incident_label = st.sidebar.selectbox(
        "Incident Type", list(INCIDENT_TYPES.keys()),
        format_func=lambda k: f"{k} – {INCIDENT_TYPES[k]}",
    )

    lane_label = st.sidebar.selectbox(
        "Lane Closure", list(LANE_CLOSURES.keys()),
        format_func=lambda k: f"{k} – {LANE_CLOSURES[k]}",
    )

    direction_encoded = st.sidebar.selectbox(
        "Direction", list(DIRECTIONS.keys()),
        format_func=lambda k: DIRECTIONS[k],
    )

    blocking_encoded = st.sidebar.selectbox("Blocking", [0, 1])
    severity_score = st.sidebar.slider("Severity Score", 1, 3, DEFAULTS["severity_default"])
    rush_blocking_interaction = int(is_rush_hour and blocking_encoded == 1)

    submitted = st.sidebar.button("🚗 Predict Impact")

    params = {
        "trip_id": st.session_state["selected_trip_id"],
        "trip_geojson": selected_trip,
        "incident_milepost": approx_mile,
        "milepost_normalized": selected_norm,

        "hour": hour,
        "day_of_week": day_of_week,
        "is_weekend": is_weekend,
        "is_rush_hour": is_rush_hour,

        "incident_type_encoded": incident_label,
        "lane_closure_encoded": lane_label,
        "direction_encoded": direction_encoded,
        "blocking_encoded": blocking_encoded,
        "severity_score": severity_score,
        "rush_blocking_interaction": rush_blocking_interaction,
    }

    return params, submitted
