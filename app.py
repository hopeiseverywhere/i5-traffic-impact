import streamlit as st

from prediction import predict_incident_impact
from util.data_loader import (
    load_mileposts,
    load_trip_segments,
    get_trip_by_id,
)
from components.sidebar import prediction_sidebar
from components.map_viz import display_unified_map


# ======================================================
# PAGE CONFIG
# ======================================================
st.set_page_config(page_title="🚧 I-5 Incident Impact Predictor", layout="wide")


# ======================================================
# LOAD DATA
# ======================================================
mileposts = load_mileposts("./geodata/i5_milepost_in_range.geojson")
trip_list = load_trip_segments("./geodata/i5_trip_segments.geojson")


# ======================================================
# INIT SESSION STATE
# ======================================================
if "selected_norm" not in st.session_state:
    st.session_state["selected_norm"] = None
if "approx_mile" not in st.session_state:
    st.session_state["approx_mile"] = None
if "prediction_result" not in st.session_state:
    st.session_state["prediction_result"] = None
if "direction_encoded" not in st.session_state:
    st.session_state["direction_encoded"] = 0
if "selected_trip_id" not in st.session_state:
    st.session_state["selected_trip_id"] = None


# AUTO RERUN WHEN START/END CHANGES
if st.session_state.get("pending_map_refresh", False):
    st.session_state["pending_map_refresh"] = False
    st.rerun()
# ======================================================
# HEADER + CSS
# ======================================================
st.title("🚧 I-5 Traffic Incident Impact Predictor")
st.caption(
    "Estimate predicted delay and affected distance using machine learning models."
)

st.markdown("""
    <style>
        .stMarkdown p, .stMarkdown h2, .stMarkdown h3, .stMarkdown h4 {
            margin-bottom: 0.2rem !important;
            margin-top: 0.4rem !important;
        }
        div[data-testid="stHorizontalBlock"] {
            flex-wrap: nowrap !important;
            justify-content: space-between !important;
        }
        [data-testid="stMetricLabel"] {
            font-size: 0.8rem !important;
        }
        [data-testid="stMetricValue"] {
            font-size: 1.3rem !important;
            font-weight: 600 !important;
        }
        div[data-testid="stHorizontalBlock"] > div {
            margin: 0.2rem !important;
            flex: 1 1 18% !important;
        }
        h2, h3 {
            margin-top: 0.6rem !important;
            margin-bottom: 0.3rem !important;
        }
    </style>
""", unsafe_allow_html=True)


# ======================================================
# SHOW PREDICTION RESULT (IF ANY)
# ======================================================
result = st.session_state["prediction_result"]

if result is not None:
    st.subheader("Prediction Summary")

    col1, col2, col3, col4, col5 = st.columns(5)
    col1.metric("Traffic Impact Severity",
                "⚠️ Yes" if result["high_impact_prediction"] else "✅ No")
    col2.metric("Severe Impact Probability",
                f"{result['high_impact_probability']*100:.1f}%")
    col3.metric("Predicted Delay",
                f"{result['predicted_delay_minutes']:.1f} min")
    col4.metric("Impact Radius",
                f"{result['impact_radius_miles']:.2f} mi")
    col5.metric("Model Certainty",
                result["confidence"])

    st.markdown("---")


# ======================================================
# RESOLVE SELECTED TRIP FEATURE (for map)
# ======================================================
selected_trip_feature = None
trip_id = st.session_state.get("selected_trip_id")

if trip_id is not None:
    selected_trip_feature = get_trip_by_id(trip_list, trip_id)


# ======================================================
# MAIN MAP
# ======================================================
st.subheader("📍 Interactive Map")

display_unified_map(
    mileposts=mileposts,
    selected_norm=st.session_state["selected_norm"],
    prediction_result=st.session_state["prediction_result"],
    direction_encoded=st.session_state["direction_encoded"],
    all_trips=trip_list,
    selected_trip_id=st.session_state["selected_trip_id"],
)

# ======================================================
# SIDEBAR — Includes trip selection now
# ======================================================
params, submitted = prediction_sidebar(
    st.session_state["selected_norm"],
    st.session_state["approx_mile"],
)

# ======================================================
# HANDLE PREDICTION BUTTON
# ======================================================
if submitted:
    # If user never clicked, use milepost from sidebar defaults
    if st.session_state["selected_norm"] is None:
        st.session_state["selected_norm"] = params["milepost_normalized"]
        st.session_state["approx_mile"] = params["incident_milepost"]

    result = predict_incident_impact(params)
    st.session_state["prediction_result"] = result
    st.session_state["direction_encoded"] = params["direction_encoded"]

    st.rerun()


# ======================================================
# FINAL INFO MESSAGE
# ======================================================
if not submitted:
    st.info(
        "Select a trip segment from the sidebar → click on the map → adjust parameters → click **Predict Impact**."
    )
