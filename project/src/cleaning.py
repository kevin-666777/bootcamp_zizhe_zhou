"""Reusable preprocessing functions for daily market data."""

from __future__ import annotations

from typing import Iterable

import pandas as pd

from src.ingestion import OHLCV_COLUMNS, validate_daily_ohlcv
from src.utils import clean_column_names


NUMERIC_COLUMNS = ["open", "high", "low", "close", "adj_close", "volume"]


def drop_missing(df: pd.DataFrame, required_columns: Iterable[str]) -> pd.DataFrame:
    """Return a copy without rows missing any required value.

    Market prices are intentionally not median-filled: an invented daily price
    would distort returns and volatility. Callers must choose the required
    fields explicitly so this policy remains visible.
    """
    columns = list(required_columns)
    missing = [column for column in columns if column not in df.columns]
    if missing:
        raise KeyError(f"Required columns were not found: {missing}")
    return df.dropna(subset=columns).copy()


def clean_daily_ohlcv(df: pd.DataFrame) -> pd.DataFrame:
    """Clean daily OHLCV records into a validated, model-ready base table.

    The function standardizes column names, parses dates and numeric fields,
    trims provenance text, keeps the last observation for duplicate dates,
    drops rows with missing or economically invalid required values, sorts by
    date, and validates the final market-data rules. The input is not mutated.
    """
    cleaned = clean_column_names(df)
    missing_columns = [column for column in OHLCV_COLUMNS if column not in cleaned.columns]
    if missing_columns:
        raise ValueError(f"Missing required columns: {missing_columns}")

    cleaned["date"] = pd.to_datetime(cleaned["date"], errors="coerce").dt.tz_localize(None)
    for column in NUMERIC_COLUMNS:
        cleaned[column] = pd.to_numeric(cleaned[column], errors="coerce")
    for column in ["symbol", "source"]:
        if column in cleaned.columns:
            cleaned[column] = cleaned[column].astype("string").str.strip()

    cleaned = cleaned.sort_values("date", kind="stable", na_position="last")
    cleaned = cleaned.drop_duplicates(subset=["date"], keep="last")
    cleaned = drop_missing(cleaned, OHLCV_COLUMNS)

    valid_prices = (cleaned[["open", "high", "low", "close", "adj_close"]] > 0).all(axis=1)
    valid_volume = cleaned["volume"] >= 0
    valid_high = cleaned["high"] >= cleaned[["open", "close", "low"]].max(axis=1)
    valid_low = cleaned["low"] <= cleaned[["open", "close", "high"]].min(axis=1)
    cleaned = cleaned.loc[valid_prices & valid_volume & valid_high & valid_low].copy()

    if cleaned.empty:
        raise ValueError("No valid OHLCV rows remain after cleaning.")
    cleaned["volume"] = cleaned["volume"].astype("int64")
    cleaned = cleaned.sort_values("date").reset_index(drop=True)
    validate_daily_ohlcv(cleaned)
    return cleaned


def cleaning_report(original: pd.DataFrame, cleaned: pd.DataFrame) -> dict[str, object]:
    """Summarize the observable impact of preprocessing."""
    original_names = clean_column_names(original)
    original_dates = pd.to_datetime(original_names.get("date"), errors="coerce")
    required_present = [column for column in OHLCV_COLUMNS if column in original_names.columns]
    return {
        "rows_before": len(original),
        "rows_after": len(cleaned),
        "rows_removed": len(original) - len(cleaned),
        "duplicate_dates_before": int(original_dates.duplicated().sum()),
        "duplicate_dates_after": int(cleaned["date"].duplicated().sum()),
        "missing_required_before": int(original_names[required_present].isna().sum().sum()),
        "missing_required_after": int(cleaned[OHLCV_COLUMNS].isna().sum().sum()),
        "date_min": cleaned["date"].min().date().isoformat(),
        "date_max": cleaned["date"].max().date().isoformat(),
    }
