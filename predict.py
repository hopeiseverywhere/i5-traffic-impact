
"""
Prediction Functions for Streamlit App
"""
import streamlit as st
import joblib
import json
import numpy as np

# -------------------------------
# Cache model loading
# -------------------------------


@st.cache_resource
def load_models():
    clf = joblib.load('models/high_impact_classifier.joblib')
    reg = joblib.load('models/delay_regressor.joblib')

    with open('models/feature_list.json', 'r') as f:
        feature_list = json.load(f)

    return clf, reg, feature_list


clf_model, reg_model, FEATURE_LIST = load_models()


with open('models/feature_list.json', 'r') as f:
    FEATURE_LIST = json.load(f)

# Severity mapping
SEVERITY_LABELS = {
    0: 'No_Delay',
    1: 'Minor (<5min)',
    2: 'Moderate (5-15min)',
    3: 'Severe (>15min)'
}


def predict_incident_impact(incident_params):
    """
    Predict impact of a traffic incident using multi-class classification
    """

    # Create feature vector
    feature_vector = []
    for feat in FEATURE_LIST:
        feature_vector.append(incident_params.get(feat, 0))

    feature_vector = np.array(feature_vector).reshape(1, -1)

    # Classification prediction (multi-class)
    severity_probs = clf_model.predict_proba(feature_vector)[0]
    severity_pred = clf_model.predict(feature_vector)[0]

    # Regression prediction
    predicted_delay = max(0, reg_model.predict(feature_vector)[0])

    # Calculate impact radius
    impact_radius = estimate_impact_radius(
        predicted_delay,
        incident_params.get('blocking_encoded', 0),
        incident_params.get('incident_type_encoded', 0)
    )

    return {
        'severity_prediction': int(severity_pred),
        'severity_label': SEVERITY_LABELS[severity_pred],
        'severity_probabilities': {
            SEVERITY_LABELS[i]: float(prob) for i, prob in enumerate(severity_probs)
        },
        'predicted_delay_minutes': float(predicted_delay),
        'impact_radius_miles': float(impact_radius),
        'confidence': 'High' if max(severity_probs) > 0.7 else 'Medium',

    }


def estimate_impact_radius(delay_minutes, blocking, incident_type):
    """Estimate affected distance"""
    base_radius = 1.0
    delay_contribution = (delay_minutes / 10) * 0.5
    blocking_multiplier = 1.5 if blocking == 1 else 1.0
    incident_multiplier = 1.3 if incident_type in [3, 4, 5] else 1.0
    radius = (base_radius + delay_contribution) * \
        blocking_multiplier * incident_multiplier
    return min(radius, 10.0)


# if __name__ == "__main__":
#     # Test prediction
#     test_incident = {
#         'hour': 16,  # 4 PM
#         'day_of_week': 2,  # Wednesday
#         'is_rush_hour': 1,
#         'is_weekend': 0,
#         'location_zone': 5,
#         'milepost_normalized': 0.5,
#         'incident_type_encoded': 3,  # Collision
#         'lane_closure_encoded': 3,   # Two lanes
#         'direction_encoded': 0,
#         'blocking_encoded': 1,
#         'severity_score': 2,
#         'rush_blocking_interaction': 1,
#     }

#     test_incident2 = {
#         "hour": 12,
#         "day_of_week": 2,
#         "month": 6,
#         "day_of_month": 15,
#         "milepost_normalized": 0.48,
#         "StartID": 1,
#         "EndID": 2,
#         "useHOV": 0,
#         "incident_type_encoded": 0,
#         "lane_closure_encoded": 0,
#         "blocking_encoded": 0,
#     }

#     result = predict_incident_impact(test_incident2)

#     print("\nTest Prediction:")
#     print(
#         f"  Severity Prediction: {result['severity_label']} ({result['severity_prediction']})")
#     print(f"\n  Severity Probabilities:")
#     for label, prob in result['severity_probabilities'].items():
#         print(f"    {label}: {prob:.2%}")
#     print(
#         f"\n  Predicted Delay: {result['predicted_delay_minutes']:.1f} minutes")
#     print(f"  Impact Radius: {result['impact_radius_miles']:.2f} miles")
#     print(f"  Confidence: {result['confidence']}")
