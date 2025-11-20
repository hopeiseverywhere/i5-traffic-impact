import streamlit as st

from predict import predict_incident_impact
from util.data_loader import (
    load_mileposts,
    load_trip_segments, load_model_metadata,
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
model_metadata = load_model_metadata("./models/model_metadata.json")

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
# SHOW PREDICTION RESULT
# ======================================================
result = st.session_state["prediction_result"]

if result is not None:

    st.subheader("Prediction Summary")

    col1, col2, col3 = st.columns(3)
    col1.metric("Severity", result["severity_label"])
    col2.metric("Predicted Delay",
                f"{result['predicted_delay_minutes']:.1f} min")
    col3.metric("Impact Radius", f"{result['impact_radius_miles']:.2f} mi")

    st.metric("Confidence Level", result["confidence"])

    st.markdown("#### Severity Class Probabilities")
    probs = result["severity_probabilities"]

    colA, colB, colC, colD = st.columns(4)

    # Normalize label ordering
    ordered_labels = [
        "No_Delay",
        "Minor (<5min)",
        "Moderate (5-15min)",
        "Severe (>15min)",
    ]

    columns = [colA, colB, colC, colD]

    for col, label in zip(columns, ordered_labels):
        pct = probs.get(label, 0) * 100
        col.metric(label, f"{pct:.1f} %")

    st.markdown("---")


# ======================================================
# RESOLVE SELECTED TRIP FEATURE
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
# AUTO RERUN WHEN START/END CHANGES
if st.session_state.get("pending_map_refresh", False):
    st.session_state["pending_map_refresh"] = False
    st.rerun()

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
    # st.session_state["direction_encoded"] = params["direction_encoded"]

    st.rerun()


# ======================================================
# FINAL INFO MESSAGE
# ======================================================
if not submitted:
    st.info(
        "Select a trip segment from the sidebar → put a pin on the map → adjust parameters → click **Predict Impact**."
    )

# ======================================================
# MODEL INFORMATION 
# ======================================================

with st.expander("🔍 Show Model Information"):
    meta = model_metadata

    st.subheader("Model Summary")

    col1, col2 = st.columns(2)

    with col1:
        st.write(f"**Model Type:** {meta.get('model_type', '—')}")
        st.write(f"**Training Date:** {meta.get('training_date', '—')}")
        st.write(f"**Training Samples:** {meta.get('training_samples', 0):,}")
        st.write(f"**Test Samples:** {meta.get('test_samples', 0):,}")
        st.write(f"**Number of Features:** {meta.get('n_features', '—')}")

    with col2:
        st.markdown("#### Classification Metrics")
        clf = meta.get("classification_metrics", {})
        st.write(f"- **F1 Score:** {clf.get('f1_score', 0):.3f}")
        st.write(f"- **ROC AUC:** {clf.get('roc_auc', 0):.3f}")

        st.markdown("#### Regression Metrics")
        reg = meta.get("regression_metrics", {})
        st.write(f"- **RMSE:** {reg.get('rmse', 0):.3f}")
        st.write(f"- **MAE:** {reg.get('mae', 0):.3f}")
        st.write(f"- **R²:** {reg.get('r2', 0):.3f}")

    st.markdown("#### Features Used")
    st.json(meta.get("features", []))
