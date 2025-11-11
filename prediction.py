import joblib
import json
import numpy as np

# ======================================================
# LOAD MODELS
# ======================================================
clf_model = joblib.load('models/high_impact_classifier.joblib')
reg_model = joblib.load('models/delay_regressor.joblib')

with open('models/feature_list.json', 'r') as f:
    FEATURE_LIST = json.load(f)


# ======================================================
# MAIN PREDICTION FUNCTION
# ======================================================
def predict_incident_impact(incident_params):
    """Predict impact of a traffic incident"""
    
    # Build feature vector
    feature_vector = np.array(
        [incident_params.get(feat, 0) for feat in FEATURE_LIST]
    ).reshape(1, -1)
    
    # Classification
    high_impact_prob = clf_model.predict_proba(feature_vector)[0, 1]
    high_impact_pred = clf_model.predict(feature_vector)[0]
    
    # Regression
    predicted_delay = max(0, reg_model.predict(feature_vector)[0])
    
    # Impact radius
    impact_radius = estimate_impact_radius(
        predicted_delay,
        incident_params.get('blocking_encoded', 0),
        incident_params.get('incident_type_encoded', 0)
    )

    # Return structured result
    return {
        'high_impact_probability': float(high_impact_prob),
        'high_impact_prediction': int(high_impact_pred),
        'predicted_delay_minutes': float(predicted_delay),
        'impact_radius_miles': float(impact_radius),
        'confidence': 'High' if high_impact_prob > 0.7 or high_impact_prob < 0.3 else 'Medium',
        # Dynamically add model names
        'classifier_name': clf_model.__class__.__name__,
        'regressor_name': reg_model.__class__.__name__,
    }


# ======================================================
# SUPPORT FUNCTION
# ======================================================
def estimate_impact_radius(delay_minutes, blocking, incident_type):
    """Estimate affected distance"""
    base_radius = 1.0
    delay_contribution = (delay_minutes / 10) * 0.5
    blocking_multiplier = 1.5 if blocking == 1 else 1.0
    incident_multiplier = 1.3 if incident_type in [3, 4, 5] else 1.0
    radius = (base_radius + delay_contribution) * blocking_multiplier * incident_multiplier
    return min(radius, 10.0)


# ======================================================
# TEST
# ======================================================
if __name__ == "__main__":
    test_incident = {
        'hour': 16,  # 4 PM
        'day_of_week': 2,  # Wednesday
        'is_rush_hour': 1,
        'is_weekend': 0,
        'location_zone': 5,
        'milepost_normalized': 0.5,
        'incident_type_encoded': 3,  # Collision
        'lane_closure_encoded': 3,   # Two lanes
        'direction_encoded': 0,
        'blocking_encoded': 1,
        'severity_score': 2,
        'rush_blocking_interaction': 1,
    }

    result = predict_incident_impact(test_incident)
    print("\nTest Prediction:")
    print(f"  High Impact Probability: {result['high_impact_probability']:.2%}")
    print(f"  High Impact Prediction: {'Yes' if result['high_impact_prediction'] else 'No'}")
    print(f"  Predicted Delay: {result['predicted_delay_minutes']:.1f} minutes")
    print(f"  Impact Radius: {result['impact_radius_miles']:.2f} miles")
    print(f"  Confidence: {result['confidence']}")
    print(f"  Classifier: {result['classifier_name']}")
    print(f"  Regressor: {result['regressor_name']}")
