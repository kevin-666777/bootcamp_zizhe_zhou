"""Flask API for the Stage 13 two-feature regression model."""

from pathlib import Path
import math

from flask import Flask, jsonify, request
import joblib


# Load the model once when the application starts, never inside a route.
MODEL_PATH = Path(__file__).resolve().parent / "model" / "model.pkl"
model = joblib.load(MODEL_PATH)
app = Flask(__name__)


def _validate_features(values):
    """Return two finite floats or an error message for invalid input."""
    if not isinstance(values, (list, tuple)) or len(values) != 2:
        return None, "'features' must be a list containing exactly two values."

    try:
        features = [float(value) for value in values]
    except (TypeError, ValueError):
        return None, "Both feature values must be numeric."

    if not all(math.isfinite(value) for value in features):
        return None, "Both feature values must be finite numbers."
    return features, None


def _prediction_response(features):
    """Predict one row and return a JSON response."""
    prediction = float(model.predict([features])[0])
    return jsonify({"prediction": prediction})


@app.route("/predict", methods=["POST"])
def predict_post():
    """Predict from a JSON body such as {"features": [0.1, 0.2]}."""
    data = request.get_json(silent=True)
    if not isinstance(data, dict) or "features" not in data:
        return jsonify({"error": "JSON body must include a 'features' key."}), 400

    features, error = _validate_features(data["features"])
    if error:
        return jsonify({"error": error}), 400
    return _prediction_response(features)


@app.route("/predict/<f1>/<f2>", methods=["GET"])
def predict_get(f1, f2):
    """Predict from two numeric URL path parameters."""
    features, error = _validate_features([f1, f2])
    if error:
        return jsonify({"error": error}), 400
    return _prediction_response(features)


if __name__ == "__main__":
    # Port 5050 avoids the macOS service that can occupy port 5000.
    app.run(host="127.0.0.1", port=5050, debug=False)
