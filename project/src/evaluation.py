"""Reproducible uncertainty and subgroup evaluation helpers."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from statistics import NormalDist

import numpy as np
import pandas as pd


def _finite_values(values: Sequence[float]) -> np.ndarray:
    array = np.asarray(values, dtype=float)
    if array.ndim != 1 or len(array) < 2:
        raise ValueError("Evaluation values must be a one-dimensional sequence with at least two rows.")
    if not np.isfinite(array).all():
        raise ValueError("Evaluation values must all be finite.")
    return array


def gaussian_mean_interval(
    values: Sequence[float], *, confidence: float = 0.95
) -> tuple[float, float, float]:
    """Return a normal-approximation confidence interval for a sample mean."""
    array = _finite_values(values)
    if not 0 < confidence < 1:
        raise ValueError("confidence must be between 0 and 1.")
    estimate = float(array.mean())
    standard_error = float(array.std(ddof=1) / np.sqrt(len(array)))
    critical_value = NormalDist().inv_cdf(0.5 + confidence / 2)
    return estimate, estimate - critical_value * standard_error, estimate + critical_value * standard_error


def bootstrap_mean_interval(
    values: Sequence[float],
    *,
    confidence: float = 0.95,
    n_bootstrap: int = 5_000,
    method: str = "iid",
    block_size: int = 20,
    random_state: int = 42,
) -> tuple[float, float, float]:
    """Return a percentile CI using IID or circular moving-block resampling."""
    array = _finite_values(values)
    if not 0 < confidence < 1:
        raise ValueError("confidence must be between 0 and 1.")
    if n_bootstrap < 100:
        raise ValueError("n_bootstrap must be at least 100.")
    if method not in {"iid", "moving_block"}:
        raise ValueError("method must be 'iid' or 'moving_block'.")
    if method == "moving_block" and (block_size < 1 or block_size > len(array)):
        raise ValueError("block_size must be between 1 and the sample size.")

    rng = np.random.default_rng(random_state)
    if method == "iid":
        indices = rng.integers(0, len(array), size=(n_bootstrap, len(array)))
    else:
        blocks_needed = int(np.ceil(len(array) / block_size))
        starts = rng.integers(0, len(array), size=(n_bootstrap, blocks_needed))
        offsets = np.arange(block_size)
        indices = ((starts[..., None] + offsets) % len(array)).reshape(n_bootstrap, -1)
        indices = indices[:, : len(array)]
    bootstrap_means = array[indices].mean(axis=1)
    alpha = 1 - confidence
    lower, upper = np.quantile(bootstrap_means, [alpha / 2, 1 - alpha / 2])
    return float(array.mean()), float(lower), float(upper)


def compare_error_intervals(
    predictions: pd.DataFrame,
    scenario_masks: Mapping[str, Sequence[bool]],
    *,
    confidence: float = 0.95,
    n_bootstrap: int = 5_000,
    block_size: int = 20,
    random_state: int = 42,
) -> pd.DataFrame:
    """Compare paired MAE differences across scenarios and CI assumptions.

    The estimand is model absolute error minus baseline absolute error. Negative
    values favor the regression; positive values favor the baseline.
    """
    required = {"absolute_error", "baseline_absolute_error"}
    missing = sorted(required.difference(predictions.columns))
    if missing:
        raise ValueError(f"Prediction error columns are missing: {missing}")
    rows: list[dict[str, object]] = []
    for scenario_index, (scenario, mask) in enumerate(scenario_masks.items()):
        mask_array = np.asarray(mask, dtype=bool)
        if len(mask_array) != len(predictions):
            raise ValueError(f"Scenario mask length does not match predictions: {scenario}")
        differences = (
            predictions.loc[mask_array, "absolute_error"]
            - predictions.loc[mask_array, "baseline_absolute_error"]
        ).to_numpy()
        if len(differences) < 2:
            raise ValueError(f"Scenario must contain at least two observations: {scenario}")
        seed = random_state + scenario_index * 100
        methods = {
            "Gaussian": gaussian_mean_interval(differences, confidence=confidence),
            "IID bootstrap": bootstrap_mean_interval(
                differences,
                confidence=confidence,
                n_bootstrap=n_bootstrap,
                method="iid",
                block_size=min(block_size, len(differences)),
                random_state=seed,
            ),
            f"Moving-block bootstrap ({min(block_size, len(differences))}d)": bootstrap_mean_interval(
                differences,
                confidence=confidence,
                n_bootstrap=n_bootstrap,
                method="moving_block",
                block_size=min(block_size, len(differences)),
                random_state=seed + 1,
            ),
        }
        for method, (estimate, lower, upper) in methods.items():
            rows.append(
                {
                    "scenario": scenario,
                    "method": method,
                    "observations": len(differences),
                    "mean_mae_difference": estimate,
                    "ci_lower": lower,
                    "ci_upper": upper,
                    "confidence": confidence,
                }
            )
    return pd.DataFrame(rows)


def subgroup_error_summary(predictions: pd.DataFrame, group_column: str) -> pd.DataFrame:
    """Summarize model and baseline errors for stakeholder-relevant subgroups."""
    required = {
        group_column,
        "actual",
        "prediction",
        "baseline",
        "absolute_error",
        "baseline_absolute_error",
    }
    missing = sorted(required.difference(predictions.columns))
    if missing:
        raise ValueError(f"Subgroup evaluation columns are missing: {missing}")
    rows = []
    for group, frame in predictions.groupby(group_column, sort=True, observed=True):
        model_mae = float(frame["absolute_error"].mean())
        baseline_mae = float(frame["baseline_absolute_error"].mean())
        rows.append(
            {
                group_column: group,
                "observations": len(frame),
                "model_mae": model_mae,
                "baseline_mae": baseline_mae,
                "mae_difference": model_mae - baseline_mae,
                "mae_improvement_pct": 100 * (baseline_mae - model_mae) / baseline_mae,
                "model_rmse": float(np.sqrt(np.mean((frame["actual"] - frame["prediction"]) ** 2))),
                "baseline_rmse": float(np.sqrt(np.mean((frame["actual"] - frame["baseline"]) ** 2))),
            }
        )
    return pd.DataFrame(rows)
