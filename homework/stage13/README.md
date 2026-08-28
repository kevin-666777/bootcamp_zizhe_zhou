# Stage 13 Homework - Prediction API

This Flask API serves a scikit-learn linear regression model trained on a reproducible, synthetic dataset with two input features. It demonstrates how a different program or a browser can request a prediction from one model loaded once at application startup.

## Files

- `homework13_productization_submission.ipynb`: model training and live API test evidence
- `model/model.pkl`: trained model saved with `joblib`
- `app.py`: Flask application with POST and GET prediction routes

## Run the API

From `homework/stage13/`, activate an environment containing Flask, scikit-learn, joblib, and requests, then run:

```bash
python app.py
```

The server starts at `http://127.0.0.1:5050`. Port 5050 is used because a macOS system service can occupy port 5000. The model is loaded from `model/model.pkl` once, when the application starts.

## POST `/predict`

Send exactly two feature values in a JSON body:

```bash
curl -X POST http://127.0.0.1:5050/predict \
  -H "Content-Type: application/json" \
  -d '{"features": [0.1, 0.2]}'
```

Response:

```json
{"prediction":23.58961171297328}
```

## GET `/predict/<f1>/<f2>`

Supply the same two values as URL parameters:

```bash
curl http://127.0.0.1:5050/predict/0.1/0.2
```

Response:

```json
{"prediction":23.58961171297328}
```

## Bad input

Invalid input returns JSON with HTTP status `400`, rather than exposing a server traceback. For example:

```bash
curl -i http://127.0.0.1:5050/predict/abc/0.2
```

Response body:

```json
{"error":"Both feature values must be numeric."}
```

The POST route also returns `400` if the JSON body is missing `features`, contains other than two feature values, or contains non-numeric/non-finite values.
