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


def expanding_window_backtest(
    data: pd.DataFrame,
    *,
    feature_columns: Sequence[str] = REGRESSION_FEATURE_COLUMNS,
    target_column: str = TARGET_COLUMN,
    initial_train_size: int = 600,
    test_size: int = 200,
    candidates: dict[str, Pipeline] | None = None,
    baseline_column: str = "rolling_vol_21d",
    tail_quantile: float = 0.8,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Run non-overlapping expanding-window folds with per-fold model selection.

    Candidate selection, scaling, fitting, and the tail threshold are recomputed
    using only observations earlier than each test window. The final fold may be
    shorter than ``test_size`` so every observation after the initial window is
    evaluated exactly once.
    """
    if initial_train_size < 10:
        raise ValueError("initial_train_size must be at least 10 observations.")
    if test_size < 1:
        raise ValueError("test_size must be positive.")
    if not 0 < tail_quantile < 1:
        raise ValueError("tail_quantile must be between 0 and 1.")
    required = ["date", *feature_columns, target_column]
    if baseline_column not in required:
        required.append(baseline_column)
    missing = [column for column in required if column not in data.columns]
    if missing:
        raise ValueError(f"Backtest columns are missing: {missing}")
    frame = data[required].copy()
    frame["date"] = pd.to_datetime(frame["date"], errors="raise")
    if frame["date"].duplicated().any() or not frame["date"].is_monotonic_increasing:
        raise ValueError("Backtest dates must be unique and sorted ascending.")
    if frame.drop(columns="date").isna().any().any():
        raise ValueError("Backtest features, target, and baseline must not contain missing values.")
    if initial_train_size >= len(frame):
        raise ValueError("initial_train_size must leave at least one test observation.")

    fold_rows: list[dict[str, object]] = []
    prediction_frames: list[pd.DataFrame] = []
    candidate_models = candidates or regression_candidates()
    for fold, test_start in enumerate(range(initial_train_size, len(frame), test_size), start=1):
        test_end = min(test_start + test_size, len(frame))
        train = frame.iloc[:test_start].copy()
        test = frame.iloc[test_start:test_end].copy()
        selected_name, fitted_model, _ = select_regression_model(
            train,
            feature_columns=feature_columns,
            target_column=target_column,
            candidates=candidate_models,
        )
        prediction = np.clip(fitted_model.predict(test[list(feature_columns)]), 0, None)
        actual = test[target_column].to_numpy()
        baseline = test[baseline_column].to_numpy()
        tail_threshold = float(train[target_column].quantile(tail_quantile))
        tail_mask = actual >= tail_threshold
        model_metrics = regression_metrics(actual, prediction)
        baseline_metrics = regression_metrics(actual, baseline)
        fold_rows.append(
            {
                "fold": fold,
                "selected_model": selected_name,
                "train_start": train["date"].iloc[0],
                "train_end": train["date"].iloc[-1],
                "test_start": test["date"].iloc[0],
                "test_end": test["date"].iloc[-1],
                "train_rows": len(train),
                "test_rows": len(test),
                "model_mae": model_metrics["mae"],
                "model_rmse": model_metrics["rmse"],
                "model_r2": model_metrics["r2"],
                "baseline_mae": baseline_metrics["mae"],
                "baseline_rmse": baseline_metrics["rmse"],
                "baseline_r2": baseline_metrics["r2"],
                "model_tail_mae": float(mean_absolute_error(actual[tail_mask], prediction[tail_mask]))
                if tail_mask.any()
                else np.nan,
                "baseline_tail_mae": float(mean_absolute_error(actual[tail_mask], baseline[tail_mask]))
                if tail_mask.any()
                else np.nan,
                "tail_threshold": tail_threshold,
                "tail_observations": int(tail_mask.sum()),
            }
        )
        prediction_frames.append(
            pd.DataFrame(
                {
                    "fold": fold,
                    "selected_model": selected_name,
                    "date": test["date"].to_numpy(),
                    "actual": actual,
                    "prediction": prediction,
                    "baseline": baseline,
                    "residual": actual - prediction,
                    "absolute_error": np.abs(actual - prediction),
                    "baseline_absolute_error": np.abs(actual - baseline),
                    "tail_threshold": tail_threshold,
                    "is_tail": tail_mask,
                }
            )
        )
    return pd.DataFrame(fold_rows), pd.concat(prediction_frames, ignore_index=True)
