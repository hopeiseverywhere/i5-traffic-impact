import streamlit as st
from util.sidebar_config import INCIDENT_TYPES, LANE_CLOSURES, DEFAULTS
from util.data_loader import load_trip_segments, get_trip_by_id
from util.segments import TRIP_SEGMENTS, SEGMENT_POINTS

# ==================================================================
# Build mapping structures
# ==================================================================

# START → set(END)
START_TO_END = {}
# (START, END) → list of trip dicts (to allow HOV/GP variants)
TRIPS_BY_SEGMENT = {}

for t in TRIP_SEGMENTS:
    s, e = t["Start"], t["End"]

    START_TO_END.setdefault(s, set()).add(e)
    TRIPS_BY_SEGMENT.setdefault((s, e), []).append(t)


# ==================================================================
# Sidebar Component
# ==================================================================
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
    # 3 CHOOSE TRIP VARIANT (GP vs HOV)
    # ======================================================
    candidate_trips = TRIPS_BY_SEGMENT[(selected_start, selected_end)]

    if len(candidate_trips) == 1:
        # Only one trip → auto select
        selected_trip_dict = candidate_trips[0]
        st.sidebar.info(
            f"Auto-selected Trip {selected_trip_dict['Id']} "
            f"({'HOV' if selected_trip_dict['UsesHOV'] else 'General Purpose'})"
        )
    else:
        # Multiple variants → user chooses GP or HOV
        variant_labels = {
            f"Trip {t['Id']} – {'HOV Lane' if t['UsesHOV'] else 'General Purpose'}": t
            for t in candidate_trips
        }

        selected_label = st.sidebar.selectbox(
            "3️⃣ Choose Trip Variant (HOV vs GP)",
            list(variant_labels.keys()),
            key="variant_selectbox",
        )

        selected_trip_dict = variant_labels[selected_label]

    # Trip ID selected
    trip_id = selected_trip_dict["Id"]

    # ======================================================
    # Confirm Trip Button
    # ======================================================
    if st.sidebar.button("✔️ Confirm Trip Selection"):
        st.session_state["selected_trip_id"] = trip_id

        # Clear previous click + prediction
        st.session_state["approx_mile"] = None
        st.session_state["selected_norm"] = None
        st.session_state["prediction_result"] = None

        # direction encoded: 0=North, 1=South
        st.session_state["direction_encoded"] = (
            0 if selected_trip_dict["Direction"] == "North" else 1
        )

        # Save HOV flag
        st.session_state["useHOV"] = selected_trip_dict["UsesHOV"]

        # Refresh map
        st.session_state["pending_map_refresh"] = True

    # ======================================================
    # Ensure confirmed trip exists
    # ======================================================
    if st.session_state.get("selected_trip_id") is None:
        st.sidebar.info(
            "➡️ Select Start → End → Variant, then click **Confirm Trip Selection**.")
        return None, False

    # Load selected trip feature (geojson)
    trips = load_trip_segments("./geodata/i5_trip_segments.geojson")
    selected_trip = get_trip_by_id(trips, st.session_state["selected_trip_id"])

    # Trip metadata
    t = next(t for t in TRIP_SEGMENTS if t["Id"]
             == st.session_state["selected_trip_id"])
    start_info = SEGMENT_POINTS[t["Start"]]
    end_info = SEGMENT_POINTS[t["End"]]
    hov_flag = 1 if t["UsesHOV"] else 0
    direction = t["Direction"]

    st.sidebar.success(
        f"🛣 **Trip {t['Id']}**\n"
        f"- **Variant:** {'HOV Lane' if hov_flag else 'General Purpose'}\n"
        f"- **Start:** {start_info['Name']} (MP {start_info['Milepost']:.2f})\n"
        f"- **End:** {end_info['Name']} (MP {end_info['Milepost']:.2f})\n"
        f"- **Direction:** {direction}"
    )

    # ======================================================
    # WAIT FOR MAP CLICK
    # ======================================================
    if approx_mile is None:
        st.sidebar.warning("📍 Click on the map to place the incident.")
        return None, False

    st.sidebar.info(
        f"📍 Incident at MP {approx_mile:.2f} (Normalized {selected_norm:.2f})")

    # ======================================================
    # MODEL FEATURE INPUTS
    # ======================================================
    hour = st.sidebar.slider("Hour (0–23)", 0, 23, DEFAULTS["hour"])
    day_of_week = st.sidebar.slider(
        "Day of Week (0=Mon)", 0, 6, DEFAULTS["day_of_week"])
    month = st.sidebar.slider("Month", 1, 12, DEFAULTS["month"])
    day_of_month = st.sidebar.slider(
        "Day of Month", 1, 31, DEFAULTS["day_of_month"])

    incident_type_encoded = st.sidebar.selectbox(
        "Incident Type",
        list(INCIDENT_TYPES.keys()),
        index=DEFAULTS["incident_type"],
        format_func=lambda k: f"{k} – {INCIDENT_TYPES[k]}"
    )

    lane_closure_encoded = st.sidebar.selectbox(
        "Lane Closure",
        list(LANE_CLOSURES.keys()),
        index=DEFAULTS["lane_closure"],
        format_func=lambda k: f"{k} – {LANE_CLOSURES[k]}"
    )

    blocking_encoded = st.sidebar.selectbox(
        "Blocking (0/1)",
        [0, 1],
        index=DEFAULTS["blocking"]
    )

    # ======================================================
    # Predict button
    # ======================================================
    submitted = st.sidebar.button("🚗 Predict Impact")

    # ======================================================
    # Package final parameters
    # ======================================================
    params = {
        "milepost_normalized": selected_norm,
        "incident_milepost": approx_mile,

        "hour": hour,
        "day_of_week": day_of_week,
        "month": month,
        "day_of_month": day_of_month,

        "StartID": selected_start,
        "EndID": selected_end,
        "useHOV": hov_flag,

        "incident_type_encoded": incident_type_encoded,
        "lane_closure_encoded": lane_closure_encoded,
        "blocking_encoded": blocking_encoded,
    }

    return params, submitted
