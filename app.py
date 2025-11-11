import streamlit as st
from prediction import predict_incident_impact
from util.data_loader import load_mileposts, load_i5_geojson
from components.sidebar import prediction_sidebar
from components.map_viz import display_prediction_map


# ======================================================
# PAGE CONFIG
# ======================================================
st.set_page_config(page_title="🚧 I-5 Incident Impact Predictor", layout="wide")

# ======================================================
# LOAD DATA
# ======================================================
mileposts = load_mileposts("./geodata/i5_milepost.geojson")
i5_line = load_i5_geojson("./geodata/i5.geojson")

# ======================================================
# SIDEBAR INPUTS
# ======================================================
params, submitted = prediction_sidebar(mileposts)

# ======================================================
# MAIN LAYOUT
# ======================================================
st.title("🚧 I-5 Traffic Incident Impact Predictor")
st.caption("Estimate predicted delay and affected distance using machine learning models.")

if submitted:
    # -----------------------------------------
    # Run model
    # -----------------------------------------
    result = predict_incident_impact(params)

    # -----------------------------------------
    # Display prediction results
    # -----------------------------------------
    st.subheader("Prediction Summary")

    col1, col2, col3, col4, col5 = st.columns(5)
    col1.metric("Traffic Impact Severity", "⚠️ Yes" if result["high_impact_prediction"] else "✅ No")
    col2.metric("Severe Impact Probability", f"{result['high_impact_probability']*100:.1f}%")
    col3.metric("Predicted Delay", f"{result['predicted_delay_minutes']:.1f} min")
    col4.metric("Impact Radius", f"{result['impact_radius_miles']:.2f} mi")
    col5.metric("Model Certainty", result["confidence"])

    st.markdown("---")

    # -----------------------------------------
    # Map visualization
    # -----------------------------------------
    st.subheader("Predicted Impact Visualization")
    display_prediction_map(
        result,
        mileposts,
        i5_line,
        params["milepost_normalized"],
        params["direction_encoded"],  # 0 = NB, 1 = SB
    )

    st.markdown("---")
    
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
                st.metric("F1 Score", f"{metadata['classification_metrics']['f1_score']:.3f}")
            with col2:
                st.metric("ROC-AUC", f"{metadata['classification_metrics']['roc_auc']:.3f}")

            # --- Regressor section ---
            st.markdown("#### Regressor Metrics")
            col3, col4 = st.columns(2)
            with col3:
                st.metric("Regressor", result["regressor_name"])
                st.metric("RMSE", f"{metadata['regression_metrics']['rmse']:.2f} min")
            with col4:
                st.metric("MAE", f"{metadata['regression_metrics']['mae']:.2f} min")
                st.metric("R²", f"{metadata['regression_metrics']['r2']:.3f}")

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
    st.info("Adjust parameters in the sidebar and click **Predict Impact** to generate results.")
