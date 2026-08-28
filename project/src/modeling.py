"""Time-aware regression helpers for next-day AAPL volatility."""

from __future__ import annotations

from dataclasses import dataclass
from collections.abc import Sequence

import numpy as np
import pandas as pd
from sklearn.base import clone
from sklearn.linear_model import LinearRegression, Ridge
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

from src.features import MODEL_FEATURE_COLUMNS, TARGET_COLUMN


# Friday is the reference category, avoiding a full weekday dummy set plus intercept.
REGRESSION_FEATURE_COLUMNS = [column for column in MODEL_FEATURE_COLUMNS if column != "weekday_fri"]


@dataclass(frozen=True)
class TimeSplit:
    """Chronological train/test partition with explicit feature metadata."""

    train: pd.DataFrame
    test: pd.DataFrame
    feature_columns: tuple[str, ...]
    target_column: str


def chronological_train_test_split(
    data: pd.DataFrame,
    *,
    feature_columns: Sequence[str] = REGRESSION_FEATURE_COLUMNS,
    target_column: str = TARGET_COLUMN,
    train_fraction: float = 0.8,
) -> TimeSplit:
    """Split sorted observations without shuffling or future leakage."""
    if not 0.5 <= train_fraction < 1:
        raise ValueError("train_fraction must be at least 0.5 and less than 1.")
    required = ["date", *feature_columns, target_column]
    missing = [column for column in required if column not in data.columns]
    if missing:
        raise ValueError(f"Modeling columns are missing: {missing}")
    frame = data[required].copy()
    frame["date"] = pd.to_datetime(frame["date"], errors="raise")
    if frame["date"].duplicated().any() or not frame["date"].is_monotonic_increasing:
        raise ValueError("Modeling dates must be unique and sorted ascending.")
    if frame[required[1:]].isna().any().any():
        raise ValueError("Modeling features and target must not contain missing values.")
    split_index = int(len(frame) * train_fraction)
    if split_index < 2 or len(frame) - split_index < 1:
        raise ValueError("Not enough rows for the requested train/test split.")
    return TimeSplit(
        train=frame.iloc[:split_index].reset_index(drop=True),
        test=frame.iloc[split_index:].reset_index(drop=True),
        feature_columns=tuple(feature_columns),
        target_column=target_column,
    )


def regression_candidates(alphas: Sequence[float] = (0.01, 0.1, 1.0, 10.0)) -> dict[str, Pipeline]:
    """Return standardized OLS and Ridge variations for automated comparison."""
    candidates: dict[str, Pipeline] = {
        "ols": Pipeline([("scale", StandardScaler()), ("model", LinearRegression())])
    }
    for alpha in alphas:
        if alpha <= 0:
            raise ValueError("Ridge alphas must be positive.")
        candidates[f"ridge_alpha_{alpha:g}"] = Pipeline(
            [("scale", StandardScaler()), ("model", Ridge(alpha=float(alpha)))]
        )
    return candidates


def regression_metrics(actual: Sequence[float], predicted: Sequence[float]) -> dict[str, float]:
    """Calculate magnitude-aware regression metrics."""
    actual_array = np.asarray(actual, dtype=float)
    predicted_array = np.asarray(predicted, dtype=float)
    return {
        "mae": float(mean_absolute_error(actual_array, predicted_array)),
        "rmse": float(np.sqrt(mean_squared_error(actual_array, predicted_array))),
        "r2": float(r2_score(actual_array, predicted_array)),
    }


def select_regression_model(
    train: pd.DataFrame,
    *,
    feature_columns: Sequence[str] = REGRESSION_FEATURE_COLUMNS,
    target_column: str = TARGET_COLUMN,
    validation_fraction: float = 0.2,
    candidates: dict[str, Pipeline] | None = None,
) -> tuple[str, Pipeline, pd.DataFrame]:
    """Select by chronological validation MAE, then refit on all training rows."""
    if not 0 < validation_fraction < 0.5:
        raise ValueError("validation_fraction must be between 0 and 0.5.")
    split_index = int(len(train) * (1 - validation_fraction))
    if split_index < 2 or len(train) - split_index < 1:
        raise ValueError("Not enough training rows for chronological validation.")
    candidate_models = candidates or regression_candidates()
    if not candidate_models:
        raise ValueError("At least one candidate model is required.")
    fit_rows, validation_rows = train.iloc[:split_index], train.iloc[split_index:]
    results = []
    for name, candidate in candidate_models.items():
        fitted = clone(candidate).fit(fit_rows[list(feature_columns)], fit_rows[target_column])
        metrics = regression_metrics(
            validation_rows[target_column], fitted.predict(validation_rows[list(feature_columns)])
        )
        results.append({"model": name, **metrics})
    comparison = pd.DataFrame(results).sort_values(["mae", "rmse", "model"]).reset_index(drop=True)
    best_name = str(comparison.loc[0, "model"])
    best_model = clone(candidate_models[best_name]).fit(
        train[list(feature_columns)], train[target_column]
    )
    return best_name, best_model, comparison


def evaluate_holdout(
    model: Pipeline,
    split: TimeSplit,
    *,
    baseline_column: str = "rolling_vol_21d",
    tail_quantile: float = 0.8,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Evaluate one untouched holdout and a training-defined high-volatility tail."""
    if baseline_column not in split.test.columns:
        raise ValueError(f"Baseline column is missing: {baseline_column}")
    if not 0 < tail_quantile < 1:
        raise ValueError("tail_quantile must be between 0 and 1.")
    actual = split.test[split.target_column].to_numpy()
    prediction = np.clip(model.predict(split.test[list(split.feature_columns)]), 0, None)
    baseline = split.test[baseline_column].to_numpy()
    errors = pd.DataFrame(
        {
            "date": split.test["date"],
            "actual": actual,
            "prediction": prediction,
            "baseline": baseline,
            "residual": actual - prediction,
            "absolute_error": np.abs(actual - prediction),
        }
    )
    model_metrics = regression_metrics(actual, prediction)
    baseline_metrics = regression_metrics(actual, baseline)
    tail_threshold = float(split.train[split.target_column].quantile(tail_quantile))
    tail_mask = actual >= tail_threshold
    summary = pd.DataFrame(
        [
            {"method": "selected_regression", **model_metrics},
            {"method": "rolling_vol_21d_baseline", **baseline_metrics},
        ]
    )
    summary["tail_mae"] = [
        float(mean_absolute_error(actual[tail_mask], prediction[tail_mask])),
        float(mean_absolute_error(actual[tail_mask], baseline[tail_mask])),
    ]
    summary["tail_threshold"] = tail_threshold
    summary["tail_observations"] = int(tail_mask.sum())
    return summary, errors


def standardized_coefficients(model: Pipeline, feature_columns: Sequence[str]) -> pd.DataFrame:
    """Return coefficients per one training-standard-deviation feature increase."""
    coefficients = np.asarray(model.named_steps["model"].coef_, dtype=float)
    if len(coefficients) != len(feature_columns):
        raise ValueError("Coefficient count does not match the feature columns.")
    return (
        pd.DataFrame({"feature": list(feature_columns), "standardized_coefficient": coefficients})
        .assign(absolute_coefficient=lambda frame: frame["standardized_coefficient"].abs())
        .sort_values("absolute_coefficient", ascending=False)
        .reset_index(drop=True)
    )
