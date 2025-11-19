import streamlit as st

from prediction import predict_incident_impact
from util.data_loader import load_mileposts, load_i5_geojson
from components.sidebar import prediction_sidebar
from components.map_viz import display_unified_map


# ======================================================
# PAGE CONFIG
# ======================================================
st.set_page_config(page_title="🚧 I-5 Incident Impact Predictor", layout="wide")


# ======================================================
# LOAD DATA
# ======================================================
mileposts = load_mileposts("./geodata/i5_milepost.geojson")
i5_line = load_i5_geojson("./geodata/i5_filtered.geojson")

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
    st.session_state["direction_encoded"] = 0  # default NB


# ======================================================
# HEADER + CSS
# ======================================================
st.title("🚧 I-5 Traffic Incident Impact Predictor")
st.caption(
    "Estimate predicted delay and affected distance using machine learning models.")
# ======================================================
# SHOW PREDICTION RESULT (IF ANY)
# ======================================================
result = st.session_state["prediction_result"]

if result is not None:
    st.subheader("Prediction Summary")

    col1, col2, col3, col4, col5 = st.columns(5)
    col1.metric(
        "Traffic Impact Severity",
        "⚠️ Yes" if result["high_impact_prediction"] else "✅ No",
    )
    col2.metric(
        "Severe Impact Probability",
        f"{result['high_impact_probability']*100:.1f}%",
    )
    col3.metric(
        "Predicted Delay",
        f"{result['predicted_delay_minutes']:.1f} min",
    )
    col4.metric(
        "Impact Radius",
        f"{result['impact_radius_miles']:.2f} mi",
    )
    col5.metric("Model Certainty", result["confidence"])

    st.markdown("---")

st.markdown("""
    <style>
        /* Reduce spacing below captions and headers */
        .stMarkdown p, .stMarkdown h2, .stMarkdown h3, .stMarkdown h4 {
            margin-bottom: 0.2rem !important;
            margin-top: 0.4rem !important;
        }
        
        /* Keep all metrics in a single row */
        div[data-testid="stHorizontalBlock"] {
            flex-wrap: nowrap !important;
            justify-content: space-between !important;
        }

        /* Adjust metric label and value sizes */
        [data-testid="stMetricLabel"] {
            font-size: 0.8rem !important;
        }
        [data-testid="stMetricValue"] {
            font-size: 1.3rem !important;
            font-weight: 600 !important;
        }

        /* Keep consistent column width so 5 fit nicely */
        div[data-testid="stHorizontalBlock"] > div {
            margin: 0.2rem !important;
            flex: 1 1 18% !important;
        }

        /* Reduce vertical gaps between sections */
        h2, h3 {
            margin-top: 0.6rem !important;
            margin-bottom: 0.3rem !important;
        }
    </style>
""", unsafe_allow_html=True)

# ======================================================
# MAIN LAYOUT: MAP + SIDEBAR
# ======================================================

# map_col, _ = st.columns([3, 1])

display_unified_map(
    mileposts,
    i5_line,
    selected_norm=st.session_state["selected_norm"],
    prediction_result=st.session_state["prediction_result"],
    direction_encoded=st.session_state["direction_encoded"],
)

# Sidebar builds params using the (possibly updated) selection
params, submitted = prediction_sidebar(
    st.session_state["selected_norm"],
    st.session_state["approx_mile"],
)

# ======================================================
# HANDLE PREDICTION BUTTON
# ======================================================
if submitted:
    # If user never clicked the map, use the default milepost for map display
    if st.session_state["selected_norm"] is None:
        st.session_state["selected_norm"] = params["milepost_normalized"]
        st.session_state["approx_mile"] = None  # optional

    result = predict_incident_impact(params)
    st.session_state["prediction_result"] = result
    st.session_state["direction_encoded"] = params["direction_encoded"]
    st.rerun()

    # -----------------------------------------
    # Model Performance Section
    # -----------------------------------------
    with st.expander("View Model Performance Details"):
        metadata = result.get("metadata", {})

        if metadata:
            # --- Classifier section ---
            st.markdown("#### Classifier Metrics")
            col1, col2 = st.columns(2)
            with col1:
                st.metric("Classifier", result["classifier_name"])
                st.metric(
                    "F1 Score",
                    f"{metadata['classification_metrics']['f1_score']:.3f}",
                )
            with col2:
                st.metric(
                    "ROC-AUC",
                    f"{metadata['classification_metrics']['roc_auc']:.3f}",
                )

            # --- Regressor section ---
            st.markdown("#### Regressor Metrics")
            col3, col4 = st.columns(2)
            with col3:
                st.metric("Regressor", result["regressor_name"])
                st.metric(
                    "RMSE",
                    f"{metadata['regression_metrics']['rmse']:.2f} min",
                )
            with col4:
                st.metric(
                    "MAE",
                    f"{metadata['regression_metrics']['mae']:.2f} min",
                )
                st.metric(
                    "R²",
                    f"{metadata['regression_metrics']['r2']:.3f}",
                )

            # --- Training info ---
            st.caption(
                f"Trained on **{metadata['training_samples']:,}** samples "
                f"(Test set: {metadata['test_samples']:,}). "
                f"Last trained: **{metadata['training_date']}**."
            )

            # --- Feature list ---
            with st.expander("View Feature List"):
                st.write(", ".join(metadata["features"]))
        else:
            st.info("Model metadata not available.")
else:
    st.info(
        "Use the marker tool on the map to choose an incident location on I-5, "
        "adjust parameters in the sidebar, and click **Predict Impact**."
    )
