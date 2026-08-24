"""Leakage-aware feature engineering for next-day AAPL volatility."""

from __future__ import annotations

from collections.abc import Sequence

import numpy as np
import pandas as pd


TARGET_COLUMN = "target_next_day_absolute_return"
WEEKDAY_COLUMNS = ["weekday_mon", "weekday_tue", "weekday_wed", "weekday_thu", "weekday_fri"]
MODEL_FEATURE_COLUMNS = [
    "return_1d",
    "return_lag_1d",
    "absolute_return_1d",
    "intraday_range_pct",
    "rolling_vol_5d",
    "rolling_vol_21d",
    "rolling_abs_return_5d",
    "volume_change_1d",
    "relative_volume_20d",
    *WEEKDAY_COLUMNS,
]

FEATURE_DEFINITIONS = {
    "return_1d": "Adjusted-close return known at the current close; captures the latest signed move.",
    "return_lag_1d": "Previous session's adjusted-close return; captures short-run continuation or reversal.",
    "absolute_return_1d": "Magnitude of the current return; volatility commonly clusters after large moves.",
    "intraday_range_pct": "(high - low) / open; Stage 08 found a strong relationship with absolute return.",
    "rolling_vol_5d": "Five-session return standard deviation; represents fast-changing recent risk.",
    "rolling_vol_21d": "Twenty-one-session return standard deviation; provides an approximately monthly baseline.",
    "rolling_abs_return_5d": "Five-session mean absolute return; a robust recent-volatility proxy.",
    "volume_change_1d": "One-session percentage change in volume; captures sudden attention or liquidity shifts.",
    "relative_volume_20d": "Current volume divided by its trailing 20-session mean; normalizes volume across eras.",
    "weekday_*": "One-hot day-of-week indicators; encode possible calendar structure without ordinal ranking.",
}


def build_volatility_features(
    df: pd.DataFrame,
    *,
    short_window: int = 5,
    long_window: int = 21,
    volume_window: int = 20,
) -> pd.DataFrame:
    """Create time-ordered features and the next-day absolute-return target.

    Every feature at row ``t`` uses information available by that session's
    close. Only the target uses row ``t+1``. Rolling calculations include the
    current observation and require complete windows; they are not backfilled.
    The input dataframe is not mutated.
    """
    if min(short_window, long_window, volume_window) < 2:
        raise ValueError("Feature windows must be at least 2 observations.")
    required = {"date", "open", "high", "low", "adj_close", "volume"}
    missing = sorted(required.difference(df.columns))
    if missing:
        raise ValueError(f"Missing feature-engineering columns: {missing}")

    featured = df.copy()
    featured["date"] = pd.to_datetime(featured["date"], errors="raise")
    if featured["date"].duplicated().any() or not featured["date"].is_monotonic_increasing:
        raise ValueError("Feature input dates must be unique and sorted ascending.")

    returns = featured["adj_close"].pct_change(fill_method=None)
    featured["return_1d"] = returns
    featured["return_lag_1d"] = returns.shift(1)
    featured["absolute_return_1d"] = returns.abs()
    featured["intraday_range_pct"] = (featured["high"] - featured["low"]) / featured["open"]
    featured["rolling_vol_5d"] = returns.rolling(short_window, min_periods=short_window).std()
    featured["rolling_vol_21d"] = returns.rolling(long_window, min_periods=long_window).std()
    featured["rolling_abs_return_5d"] = returns.abs().rolling(
        short_window, min_periods=short_window
    ).mean()
    featured["volume_change_1d"] = featured["volume"].pct_change(fill_method=None)
    trailing_volume = featured["volume"].rolling(
        volume_window, min_periods=volume_window
    ).mean()
    featured["relative_volume_20d"] = featured["volume"] / trailing_volume

    weekday = featured["date"].dt.dayofweek
    for day_number, column in enumerate(WEEKDAY_COLUMNS):
        featured[column] = weekday.eq(day_number).astype("int8")

    featured[TARGET_COLUMN] = returns.abs().shift(-1)
    featured.replace([np.inf, -np.inf], np.nan, inplace=True)
    return featured


def make_modeling_table(
    featured: pd.DataFrame,
    feature_columns: Sequence[str] = MODEL_FEATURE_COLUMNS,
    target_column: str = TARGET_COLUMN,
) -> pd.DataFrame:
    """Select complete feature/target rows while preserving date order."""
    selected = ["date", *feature_columns, target_column]
    missing = [column for column in selected if column not in featured.columns]
    if missing:
        raise ValueError(f"Modeling columns are missing: {missing}")
    table = featured[selected].dropna().copy()
    if table.empty:
        raise ValueError("No complete modeling rows remain after feature warm-up.")
    if not table["date"].is_monotonic_increasing:
        raise ValueError("Modeling rows must remain time ordered.")
    return table.reset_index(drop=True)
