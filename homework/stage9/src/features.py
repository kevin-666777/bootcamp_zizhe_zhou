"""Leakage-aware feature engineering for daily OHLCV data."""

from collections.abc import Sequence

import numpy as np
import pandas as pd


REQUIRED_COLUMNS = ("date", "open", "high", "low", "close", "volume")


def _validate_market_data(df: pd.DataFrame, required: Sequence[str] = REQUIRED_COLUMNS) -> None:
    """Validate the minimum schema and ordering keys for market features."""
    if not isinstance(df, pd.DataFrame):
        raise TypeError("df must be a pandas DataFrame")
    if df.empty:
        raise ValueError("df must contain at least one row")
    missing = [column for column in required if column not in df.columns]
    if missing:
        raise KeyError(f"Missing required market columns: {missing}")
    if df["date"].duplicated().any():
        raise ValueError("date must be unique before building time-series features")


def add_weekday_one_hot(df: pd.DataFrame) -> pd.DataFrame:
    """Return a copy with weekday text and deterministic one-hot columns."""
    result = df.copy()
    dates = pd.to_datetime(result["date"], errors="raise")
    result["weekday"] = dates.dt.day_name().astype("string")
    weekday_order = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"]
    encoded = pd.get_dummies(result["weekday"], prefix="weekday", dtype=int)
    for weekday in weekday_order:
        column = f"weekday_{weekday}"
        if column not in encoded.columns:
            encoded[column] = 0
    encoded = encoded[[f"weekday_{weekday}" for weekday in weekday_order]]
    return pd.concat([result, encoded], axis=1)


def build_market_features(df: pd.DataFrame, volatility_window: int = 5) -> pd.DataFrame:
    """Build next-day-volatility features using only current and past rows.

    The target is next trading day's absolute close-to-close return. Features
    at row ``t`` use data no later than row ``t``. Initial rolling/lag rows and
    the final target row remain missing so callers can drop them explicitly.
    """
    _validate_market_data(df)
    if not isinstance(volatility_window, int) or volatility_window < 2:
        raise ValueError("volatility_window must be an integer of at least 2")

    result = df.copy()
    result["date"] = pd.to_datetime(result["date"], errors="raise")
    result = result.sort_values("date").reset_index(drop=True)
    numeric_columns = ["open", "high", "low", "close", "volume"]
    for column in numeric_columns:
        result[column] = pd.to_numeric(result[column], errors="raise")

    result["return_1d"] = result["close"].pct_change()
    result["return_lag_1"] = result["return_1d"]
    result["absolute_return_lag_1"] = result["return_1d"].abs()
    result["rolling_volatility_5d"] = result["return_1d"].rolling(
        volatility_window, min_periods=volatility_window
    ).std(ddof=0)
    result["volume_change_1d"] = result["volume"].pct_change()
    result["intraday_range_pct"] = (result["high"] - result["low"]) / result["open"]
    rolling_close = result["close"].rolling(volatility_window, min_periods=volatility_window).mean()
    result["close_vs_5d_mean"] = result["close"] / rolling_close - 1
    result["target_next_day_abs_return"] = result["return_1d"].shift(-1).abs()

    result = add_weekday_one_hot(result)
    feature_columns = [
        "return_lag_1",
        "absolute_return_lag_1",
        "rolling_volatility_5d",
        "volume_change_1d",
        "intraday_range_pct",
        "close_vs_5d_mean",
    ]
    if np.isinf(result[feature_columns].to_numpy(dtype=float)).any():
        raise ValueError("Engineered features contain infinite values")
    return result
