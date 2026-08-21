"""Reusable outlier detection and treatment functions."""

import numpy as np
import pandas as pd


def _validate_numeric_series(series: pd.Series) -> pd.Series:
    """Validate and return a numeric, non-empty pandas Series."""
    if not isinstance(series, pd.Series):
        raise TypeError("series must be a pandas Series")
    if series.empty or series.dropna().empty:
        raise ValueError("series must contain at least one non-missing value")
    if not pd.api.types.is_numeric_dtype(series):
        raise TypeError("series must have a numeric dtype")
    return series


def detect_outliers_iqr(series: pd.Series, k: float = 1.5) -> pd.Series:
    """Return a boolean mask for values outside the Tukey IQR fences.

    Quartiles ignore missing values. Missing observations are returned as
    ``False`` because missingness is not itself evidence of an outlier.
    ``k`` must be positive; 1.5 is the conventional exploratory threshold.
    """
    values = _validate_numeric_series(series)
    if not np.isfinite(k) or k <= 0:
        raise ValueError("k must be a positive finite number")
    q1, q3 = values.quantile([0.25, 0.75])
    iqr = q3 - q1
    lower = q1 - k * iqr
    upper = q3 + k * iqr
    return ((values < lower) | (values > upper)).fillna(False)


def detect_outliers_zscore(series: pd.Series, threshold: float = 3.0) -> pd.Series:
    """Return a boolean mask where absolute population Z-score exceeds a threshold.

    Mean and population standard deviation (``ddof=0``) ignore missing values.
    Missing observations return ``False``. A constant series contains no
    Z-score outliers and therefore returns an all-False mask.
    """
    values = _validate_numeric_series(series)
    if not np.isfinite(threshold) or threshold <= 0:
        raise ValueError("threshold must be a positive finite number")
    standard_deviation = values.std(ddof=0)
    if standard_deviation == 0 or pd.isna(standard_deviation):
        return pd.Series(False, index=values.index, dtype=bool)
    z_scores = (values - values.mean()) / standard_deviation
    return (z_scores.abs() > threshold).fillna(False)


def winsorize_series(
    series: pd.Series,
    lower: float = 0.05,
    upper: float = 0.95,
) -> pd.Series:
    """Return a copy clipped to the requested lower and upper quantiles.

    Bounds must satisfy ``0 <= lower < upper <= 1``. Quantiles ignore missing
    values, while missing observations remain missing in the returned Series.
    """
    values = _validate_numeric_series(series)
    if not 0 <= lower < upper <= 1:
        raise ValueError("bounds must satisfy 0 <= lower < upper <= 1")
    lower_value = values.quantile(lower)
    upper_value = values.quantile(upper)
    return values.clip(lower=lower_value, upper=upper_value)
