import json
import numpy as np
import joblib
import streamlit as st


# ======================================================
# CACHED LOADERS
# ======================================================
@st.cache_resource
def load_model(path: str):
    """Load model from joblib (cached)."""
    return joblib.load(path)


@st.cache_data
def load_feature_list(path: str):
    """Load list of model features (cached)."""
    with open(path, "r") as f:
        return json.load(f)


@st.cache_data
def load_metadata(path: str):
    """Load model metadata (cached, from JSON file)."""
    try:
        with open(path, "r") as f:
            return json.load(f)
    except FileNotFoundError:
        return {}


# ======================================================
# INITIALIZATION 
# ======================================================
clf_model = load_model("models/high_impact_classifier.joblib")
reg_model = load_model("models/delay_regressor.joblib")
FEATURE_LIST = load_feature_list("models/feature_list.json")
MODEL_METADATA = load_metadata("models/model_metadata.json")


# ======================================================
# MAIN PREDICTION FUNCTION
# ======================================================
def predict_incident_impact(incident_params: dict) -> dict:
    """Predict impact of a traffic incident."""

    # Build feature vector (ordered to match training)
    feature_vector = np.array(
        [incident_params.get(feat, 0) for feat in FEATURE_LIST]
    ).reshape(1, -1)

    # --- Classification ---
    high_impact_prob = clf_model.predict_proba(feature_vector)[0, 1]
    high_impact_pred = clf_model.predict(feature_vector)[0]

    # --- Regression ---
    predicted_delay = max(0, reg_model.predict(feature_vector)[0])

    # --- Derived radius ---
    impact_radius = estimate_impact_radius(
        predicted_delay,
        incident_params.get("blocking_encoded", 0),
        incident_params.get("incident_type_encoded", 0),
    )

    return {
        "high_impact_probability": float(high_impact_prob),
        "high_impact_prediction": int(high_impact_pred),
        "predicted_delay_minutes": float(predicted_delay),
        "impact_radius_miles": float(impact_radius),
        "confidence": "High" if high_impact_prob > 0.7 or high_impact_prob < 0.3 else "Medium",
        "classifier_name": clf_model.__class__.__name__,
        "regressor_name": reg_model.__class__.__name__,
        "metadata": MODEL_METADATA,
    }


# ======================================================
# SUPPORT FUNCTION
# ======================================================
def estimate_impact_radius(delay_minutes, blocking, incident_type):
    """Estimate affected distance in miles."""
    base_radius = 1.0
    delay_contribution = (delay_minutes / 10) * 0.5
    blocking_multiplier = 1.5 if blocking == 1 else 1.0
    incident_multiplier = 1.3 if incident_type in [3, 4, 5] else 1.0
    radius = (base_radius + delay_contribution) * blocking_multiplier * incident_multiplier
    return min(radius, 10.0)


# ======================================================
# LOCAL TEST MODE
# ======================================================
if __name__ == "__main__":
    test_incident = {
        "hour": 16,  # 4 PM
        "day_of_week": 2,  # Wednesday
        "is_rush_hour": 1,
        "is_weekend": 0,
        "location_zone": 5,
        "milepost_normalized": 0.5,
        "incident_type_encoded": 3,  # Collision
        "lane_closure_encoded": 3,   # Two lanes
        "direction_encoded": 0,
        "blocking_encoded": 1,
        "severity_score": 2,
        "rush_blocking_interaction": 1,
    }

    result = predict_incident_impact(test_incident)

    print("\n=== Test Prediction ===")
    print(f"High Impact Probability: {result['high_impact_probability']:.2%}")
    print(f"High Impact Prediction: {'Yes' if result['high_impact_prediction'] else 'No'}")
    print(f"Predicted Delay: {result['predicted_delay_minutes']:.1f} min")
    print(f"Impact Radius: {result['impact_radius_miles']:.2f} mi")
    print(f"Confidence: {result['confidence']}")
    print(f"Classifier: {result['classifier_name']}")
    print(f"Regressor: {result['regressor_name']}")

    if result.get("metadata"):
        m = result["metadata"]
        print("\n=== Model Metadata ===")
        print(f"Type: {m['model_type']}")
        print(f"Features Used: {m['n_features']} → {', '.join(m['features'])}")
        print(f"F1 Score: {m['classification_metrics']['f1_score']:.3f}")
        print(f"ROC-AUC: {m['classification_metrics']['roc_auc']:.3f}")
        print(f"RMSE: {m['regression_metrics']['rmse']:.2f} min")
        print(f"MAE: {m['regression_metrics']['mae']:.2f} min")
        print(f"R²: {m['regression_metrics']['r2']:.3f}")
        print(f"Training Samples: {m['training_samples']:,}")
        print(f"Test Samples: {m['test_samples']:,}")
        print(f"Training Date: {m['training_date']}")
