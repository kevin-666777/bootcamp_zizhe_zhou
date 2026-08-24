"""Reusable outlier detection and sensitivity-analysis utilities."""

from __future__ import annotations

import numpy as np
import pandas as pd


def detect_outliers_iqr(series: pd.Series, k: float = 1.5) -> pd.Series:
    """Flag observations outside ``[Q1 - k*IQR, Q3 + k*IQR]``.

    Missing values are not flagged. The returned boolean Series preserves the
    original index, making it safe to assign directly to a dataframe.
    """
    if k <= 0:
        raise ValueError("k must be positive.")
    numeric = pd.to_numeric(series, errors="coerce")
    q1, q3 = numeric.quantile([0.25, 0.75])
    iqr = q3 - q1
    if pd.isna(iqr):
        return pd.Series(False, index=series.index, dtype=bool)
    lower, upper = q1 - k * iqr, q3 + k * iqr
    return ((numeric < lower) | (numeric > upper)).fillna(False).astype(bool)


def detect_outliers_zscore(series: pd.Series, threshold: float = 3.0) -> pd.Series:
    """Flag absolute population Z-scores above ``threshold``.

    A constant or all-missing series produces no flags rather than dividing by
    zero. Z-score detection assumes an approximately symmetric distribution.
    """
    if threshold <= 0:
        raise ValueError("threshold must be positive.")
    numeric = pd.to_numeric(series, errors="coerce")
    standard_deviation = numeric.std(ddof=0)
    if pd.isna(standard_deviation) or np.isclose(standard_deviation, 0.0):
        return pd.Series(False, index=series.index, dtype=bool)
    zscores = (numeric - numeric.mean()) / standard_deviation
    return zscores.abs().gt(threshold).fillna(False).astype(bool)


def winsorize_series(series: pd.Series, lower: float = 0.01, upper: float = 0.99) -> pd.Series:
    """Clip numeric values to empirical lower and upper quantiles."""
    if not 0 <= lower < upper <= 1:
        raise ValueError("Quantiles must satisfy 0 <= lower < upper <= 1.")
    numeric = pd.to_numeric(series, errors="coerce")
    lower_bound, upper_bound = numeric.quantile([lower, upper])
    return numeric.clip(lower=lower_bound, upper=upper_bound)


def flag_outliers(
    df: pd.DataFrame,
    column: str,
    *,
    method: str = "iqr",
    threshold: float = 1.5,
    flag_column: str | None = None,
) -> pd.DataFrame:
    """Return a dataframe copy with a documented boolean outlier flag."""
    if column not in df.columns:
        raise KeyError(f"Outlier column {column!r} was not found.")
    if method == "iqr":
        flags = detect_outliers_iqr(df[column], k=threshold)
    elif method == "zscore":
        flags = detect_outliers_zscore(df[column], threshold=threshold)
    else:
        raise ValueError("method must be 'iqr' or 'zscore'.")

    result = df.copy()
    result[flag_column or f"{column}_outlier_{method}"] = flags
    return result


def sensitivity_summary(
    series: pd.Series,
    outlier_flags: pd.Series,
    *,
    winsor_lower: float = 0.01,
    winsor_upper: float = 0.99,
) -> pd.DataFrame:
    """Compare summary statistics for all, filtered, and winsorized values."""
    numeric = pd.to_numeric(series, errors="coerce")
    flags = outlier_flags.reindex(numeric.index, fill_value=False).astype(bool)
    variants = {
        "all": numeric,
        "iqr_filtered": numeric.loc[~flags],
        "winsorized_1_99": winsorize_series(numeric, winsor_lower, winsor_upper),
    }
    rows = []
    for treatment, values in variants.items():
        rows.append(
            {
                "treatment": treatment,
                "count": int(values.count()),
                "mean": values.mean(),
                "median": values.median(),
                "std": values.std(),
                "min": values.min(),
                "max": values.max(),
            }
        )
    return pd.DataFrame(rows).set_index("treatment")
