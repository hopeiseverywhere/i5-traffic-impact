import streamlit as st
from util.sidebar_config import INCIDENT_TYPES, LANE_CLOSURES, DIRECTIONS, DEFAULTS
from util.data_loader import load_trip_segments, get_trip_by_id
from util.segments import TRIP_SEGMENTS, SEGMENT_POINTS

# Build mapping (Start, End) -> TripId
TRIP_MAP = {(t["Start"], t["End"]): t["Id"] for t in TRIP_SEGMENTS}

# Build mapping Start -> set of valid End points
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
    # 1️⃣ SELECT START — persistent but validated
    # ======================================================
    start_options = sorted(START_TO_END.keys())

    # Initialize stored value if missing
    if "selected_start" not in st.session_state:
        st.session_state["selected_start"] = start_options[0]

    # Render start select
    selected_start = st.sidebar.selectbox(
        "1️⃣ Select Start Location",
        start_options,
        index=start_options.index(st.session_state["selected_start"]),
        format_func=lambda sid: SEGMENT_POINTS[sid]["Name"],
        key="start_selectbox",
    )

    # Detect change → reset end selection
    if selected_start != st.session_state["selected_start"]:
        end_candidates = sorted(START_TO_END[selected_start])
        st.session_state["selected_end"] = end_candidates[0]

    st.session_state["selected_start"] = selected_start

    # ======================================================
    # 2️⃣ SELECT END — persistent but reset-safe
    # ======================================================
    end_options = sorted(START_TO_END[selected_start])

    # Fix invalid stored end if switching start
    if "selected_end" not in st.session_state or st.session_state["selected_end"] not in end_options:
        st.session_state["selected_end"] = end_options[0]

    selected_end = st.sidebar.selectbox(
        "2️⃣ Select Destination",
        end_options,
        index=end_options.index(st.session_state["selected_end"]),
        format_func=lambda eid: SEGMENT_POINTS[eid]["Name"],
        key="end_selectbox",
    )
    st.session_state["selected_end"] = selected_end

    # ======================================================
    # RESOLVE TRIP ID
    # ======================================================
    selected_trip_id = TRIP_MAP[(selected_start, selected_end)]
    st.session_state["selected_trip_id"] = selected_trip_id

    # Load trip geojson to show metadata
    trips = load_trip_segments("./geodata/i5_trip_segments.geojson")
    selected_trip = get_trip_by_id(trips, selected_trip_id)

    # Metadata
    start_info = SEGMENT_POINTS[selected_start]
    end_info = SEGMENT_POINTS[selected_end]
    hov_flag = next(t for t in TRIP_SEGMENTS if t["Id"] == selected_trip_id)["UsesHOV"]
    hov_label = "HOV Lane" if hov_flag else "General Purpose"

    # Summary
    st.sidebar.success(
        f"🛣 **Trip {selected_trip_id}**\n"
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

    # We HAVE an incident click → show full sidebar
    st.sidebar.info(f"📍 Incident at MP {approx_mile:.2f} (norm {selected_norm:.3f})")

    # ======================================================
    # TIME FEATURE INPUTS
    # ======================================================
    hour = st.sidebar.slider("Hour", 0, 23, DEFAULTS["hour"])
    day_of_week = st.sidebar.slider("Day of Week", 0, 6, DEFAULTS["day_of_week"])

    is_weekend = int(day_of_week >= 5)
    is_rush_hour = int((not is_weekend) and (7 <= hour <= 10 or 16 <= hour <= 19))

    st.sidebar.caption(
        f"{'🚦 Rush Hour' if is_rush_hour else 'Off-Peak'} · "
        f"{'Weekend' if is_weekend else 'Weekday'}"
    )

    # ======================================================
    # INCIDENT FEATURE INPUTS
    # ======================================================
    incident_label = st.sidebar.selectbox(
        "Incident Type",
        list(INCIDENT_TYPES.keys()),
        format_func=lambda k: f"{k} – {INCIDENT_TYPES[k]}",
    )

    lane_label = st.sidebar.selectbox(
        "Lane Closure",
        list(LANE_CLOSURES.keys()),
        format_func=lambda k: f"{k} – {LANE_CLOSURES[k]}",
    )

    direction_encoded = st.sidebar.selectbox(
        "Direction (Model Input)",
        list(DIRECTIONS.keys()),
        format_func=lambda k: DIRECTIONS[k],
    )

    blocking_encoded = st.sidebar.selectbox("Blocking", [0, 1])
    severity_score = st.sidebar.slider("Severity Score", 1, 3, DEFAULTS["severity_default"])

    rush_blocking_interaction = int(is_rush_hour and blocking_encoded == 1)

    submitted = st.sidebar.button("🚗 Predict Impact")

    # ======================================================
    # FINAL PARAM PACK
    # ======================================================
    params = {
        "trip_id": selected_trip_id,
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
