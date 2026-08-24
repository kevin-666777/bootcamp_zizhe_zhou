"""Market-data acquisition, validation, and raw snapshot utilities."""

from __future__ import annotations

import re
from pathlib import Path

import pandas as pd


OHLCV_COLUMNS = ["date", "open", "high", "low", "close", "adj_close", "volume"]


def fetch_daily_ohlcv(symbol: str, start: str, end: str) -> pd.DataFrame:
    """Download unadjusted daily OHLCV data from Yahoo Finance.

    ``end`` follows yfinance's exclusive-end convention. The returned schema
    is normalized so downstream project code does not depend on vendor labels.
    Network and empty-response failures raise clear exceptions.
    """
    if not re.fullmatch(r"[A-Za-z0-9.^=-]+", symbol):
        raise ValueError(f"Unsupported ticker symbol: {symbol!r}")
    if pd.Timestamp(start) >= pd.Timestamp(end):
        raise ValueError("start must be earlier than end.")

    try:
        import yfinance as yf

        frame = yf.download(
            symbol.upper(),
            start=start,
            end=end,
            interval="1d",
            auto_adjust=False,
            actions=False,
            progress=False,
            threads=False,
            timeout=30,
        )
    except Exception as exc:
        raise RuntimeError(f"Yahoo Finance request failed for {symbol!r}.") from exc

    if frame.empty:
        raise RuntimeError(
            f"Yahoo Finance returned no rows for {symbol!r} from {start} to {end}."
        )

    if isinstance(frame.columns, pd.MultiIndex):
        frame.columns = frame.columns.get_level_values(0)

    normalized = frame.reset_index().rename(
        columns={
            "Date": "date",
            "Open": "open",
            "High": "high",
            "Low": "low",
            "Close": "close",
            "Adj Close": "adj_close",
            "Volume": "volume",
        }
    )
    normalized = normalized[OHLCV_COLUMNS].copy()
    normalized["date"] = pd.to_datetime(normalized["date"]).dt.tz_localize(None)
    for column in OHLCV_COLUMNS[1:-1]:
        normalized[column] = pd.to_numeric(normalized[column], errors="raise")
    normalized["volume"] = pd.to_numeric(normalized["volume"], errors="raise").astype("int64")
    normalized["symbol"] = symbol.upper()
    normalized["source"] = "Yahoo Finance via yfinance"
    return normalized.sort_values("date", ignore_index=True)


def validate_daily_ohlcv(df: pd.DataFrame) -> dict[str, object]:
    """Validate an OHLCV dataframe and return an audit-friendly report.

    Raises:
        ValueError: If schema, missingness, uniqueness, ordering, or basic
            market-data rules fail.
    """
    missing_columns = [column for column in OHLCV_COLUMNS if column not in df.columns]
    if missing_columns:
        raise ValueError(f"Missing required columns: {missing_columns}")
    if df.empty:
        raise ValueError("OHLCV data must contain at least one row.")

    required = df[OHLCV_COLUMNS]
    na_counts = required.isna().sum()
    if int(na_counts.sum()) > 0:
        raise ValueError(f"Required columns contain missing values: {na_counts.to_dict()}")
    if not pd.api.types.is_datetime64_any_dtype(df["date"]):
        raise ValueError("date must have a pandas datetime dtype.")
    if df["date"].duplicated().any():
        raise ValueError("date values must be unique.")
    if not df["date"].is_monotonic_increasing:
        raise ValueError("date values must be sorted in increasing order.")

    price_columns = ["open", "high", "low", "close", "adj_close"]
    if (df[price_columns] <= 0).any().any():
        raise ValueError("OHLC and adjusted-close prices must be positive.")
    if (df["volume"] < 0).any():
        raise ValueError("volume must be non-negative.")
    if (df["high"] < df[["open", "close", "low"]].max(axis=1)).any():
        raise ValueError("high must be at least as large as open, close, and low.")
    if (df["low"] > df[["open", "close", "high"]].min(axis=1)).any():
        raise ValueError("low must be no greater than open, close, and high.")

    return {
        "valid": True,
        "shape": df.shape,
        "date_min": df["date"].min().date().isoformat(),
        "date_max": df["date"].max().date().isoformat(),
        "duplicate_dates": int(df["date"].duplicated().sum()),
        "na_counts": na_counts.to_dict(),
    }


def save_raw_snapshot(df: pd.DataFrame, output_dir: str | Path, symbol: str) -> Path:
    """Validate and save one deterministic, date-ranged raw CSV snapshot."""
    report = validate_daily_ohlcv(df)
    directory = Path(output_dir)
    directory.mkdir(parents=True, exist_ok=True)
    safe_symbol = re.sub(r"[^A-Za-z0-9]+", "_", symbol).strip("_").lower()
    filename = f"{safe_symbol}_ohlcv_{report['date_min'].replace('-', '')}_{report['date_max'].replace('-', '')}.csv"
    path = directory / filename
    df.to_csv(path, index=False, date_format="%Y-%m-%d")
    return path
