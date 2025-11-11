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
st.title("🚦 I-5 Traffic Incident Impact Predictor")
st.caption("Estimate predicted delay and affected distance using machine learning models.")

if submitted:
    # -----------------------------------------
    # Run model
    # -----------------------------------------
    result = predict_incident_impact(params)

    # -----------------------------------------
    # Display prediction results
    # -----------------------------------------
    st.subheader("📊 Prediction Summary")

    col1, col2, col3, col4, col5 = st.columns(5)
    col1.metric("High Impact Prediction", "✅ Yes" if result["high_impact_prediction"] else "❌ No")
    col2.metric("High Impact Probability", f"{result['high_impact_probability']*100:.1f}%")
    col3.metric("Predicted Delay", f"{result['predicted_delay_minutes']:.1f} min")
    col4.metric("Impact Radius", f"{result['impact_radius_miles']:.2f} mi")
    col5.metric("Confidence", result["confidence"])

    # Progress bar
    st.progress(result["high_impact_probability"])

    # -----------------------------------------
    # Model info (just names)
    # -----------------------------------------
    st.markdown(f"""
        **Model Info**
        - Classifier: `{result['classifier_name']}`
        - Regressor: `{result['regressor_name']}`
        """)

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

else:
    st.info("Adjust parameters in the sidebar and click **Predict Impact** to generate results.")
