"""Confidence-interval and metric utilities for model evaluation."""

from __future__ import annotations

from collections.abc import Callable

import numpy as np
from scipy import stats


Metric = Callable[[np.ndarray, np.ndarray], float]


def gaussian_mean_ci(
    values: np.ndarray,
    *,
    confidence: float = 0.95,
) -> tuple[float, float]:
    """Return a Gaussian CI for a sample mean using its standard error."""
    sample = np.asarray(values, dtype=float)
    sample = sample[np.isfinite(sample)]
    if sample.size < 2:
        raise ValueError("At least two finite observations are required.")
    if not 0 < confidence < 1:
        raise ValueError("confidence must be between 0 and 1.")
    alpha = 1 - confidence
    critical_value = stats.norm.ppf(1 - alpha / 2)
    margin = critical_value * sample.std(ddof=1) / np.sqrt(sample.size)
    mean = sample.mean()
    return float(mean - margin), float(mean + margin)


def percentile_ci(
    bootstrap_values: np.ndarray,
    *,
    confidence: float = 0.95,
) -> tuple[float, float]:
    """Return a two-sided percentile interval from bootstrap estimates."""
    values = np.asarray(bootstrap_values, dtype=float)
    values = values[np.isfinite(values)]
    if values.size < 2:
        raise ValueError("At least two finite bootstrap estimates are required.")
    if not 0 < confidence < 1:
        raise ValueError("confidence must be between 0 and 1.")
    alpha = 1 - confidence
    lower, upper = np.quantile(values, [alpha / 2, 1 - alpha / 2])
    return float(lower), float(upper)


def bootstrap_metric(
    y_true: np.ndarray,
    y_pred: np.ndarray,
    metric: Metric,
    *,
    n_boot: int = 2_000,
    random_state: int = 7,
) -> np.ndarray:
    """IID-resample paired observations and return metric estimates."""
    actual, predicted = _validate_pairs(y_true, y_pred)
    if n_boot < 500:
        raise ValueError("Use at least 500 bootstrap resamples for stable coursework estimates.")
    rng = np.random.default_rng(random_state)
    estimates = np.empty(n_boot, dtype=float)
    for iteration in range(n_boot):
        indices = rng.integers(0, actual.size, size=actual.size)
        estimates[iteration] = metric(actual[indices], predicted[indices])
    return estimates


def moving_block_bootstrap_metric(
    y_true: np.ndarray,
    y_pred: np.ndarray,
    metric: Metric,
    *,
    block_size: int = 5,
    n_boot: int = 2_000,
    random_state: int = 7,
) -> np.ndarray:
    """Circular moving-block bootstrap preserving short local dependence."""
    actual, predicted = _validate_pairs(y_true, y_pred)
    if n_boot < 500:
        raise ValueError("Use at least 500 bootstrap resamples for stable coursework estimates.")
    if not 1 <= block_size <= actual.size:
        raise ValueError("block_size must be between 1 and the sample size.")
    rng = np.random.default_rng(random_state)
    estimates = np.empty(n_boot, dtype=float)
    offsets = np.arange(block_size)
    blocks_needed = int(np.ceil(actual.size / block_size))
    for iteration in range(n_boot):
        starts = rng.integers(0, actual.size, size=blocks_needed)
        indices = ((starts[:, None] + offsets) % actual.size).ravel()[: actual.size]
        estimates[iteration] = metric(actual[indices], predicted[indices])
    return estimates


def _validate_pairs(
    y_true: np.ndarray,
    y_pred: np.ndarray,
) -> tuple[np.ndarray, np.ndarray]:
    actual = np.asarray(y_true, dtype=float)
    predicted = np.asarray(y_pred, dtype=float)
    if actual.ndim != 1 or predicted.ndim != 1:
        raise ValueError("y_true and y_pred must be one-dimensional.")
    if actual.size != predicted.size or actual.size < 2:
        raise ValueError("y_true and y_pred must have equal length of at least two.")
    if not np.isfinite(actual).all() or not np.isfinite(predicted).all():
        raise ValueError("y_true and y_pred must contain only finite values.")
    return actual, predicted
