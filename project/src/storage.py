"""Environment-friendly dataframe storage and round-trip validation."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Iterable

import pandas as pd


SUPPORTED_SUFFIXES = {".csv", ".parquet"}


def write_df(df: pd.DataFrame, path: str | Path, **kwargs: Any) -> Path:
    """Write a dataframe based on the destination suffix.

    Parent directories are created automatically. CSV files omit the index by
    default. Parquet files require ``pyarrow`` or ``fastparquet``; a missing
    engine is reported with an installation hint.
    """
    destination = Path(path).expanduser()
    suffix = destination.suffix.lower()
    if suffix not in SUPPORTED_SUFFIXES:
        raise ValueError(f"Unsupported file suffix {suffix!r}; use .csv or .parquet.")
    destination.parent.mkdir(parents=True, exist_ok=True)

    options = {"index": False, **kwargs}
    if suffix == ".csv":
        df.to_csv(destination, **options)
    else:
        try:
            df.to_parquet(destination, **options)
        except ImportError as exc:
            raise RuntimeError(
                "Writing Parquet requires pyarrow or fastparquet. "
                "Install project dependencies with `python -m pip install -r requirements.txt`."
            ) from exc
    return destination


def read_df(path: str | Path, **kwargs: Any) -> pd.DataFrame:
    """Read a CSV or Parquet dataframe based on the file suffix."""
    source = Path(path).expanduser()
    if not source.is_file():
        raise FileNotFoundError(f"Data file does not exist: {source}")
    suffix = source.suffix.lower()
    if suffix not in SUPPORTED_SUFFIXES:
        raise ValueError(f"Unsupported file suffix {suffix!r}; use .csv or .parquet.")

    if suffix == ".csv":
        return pd.read_csv(source, **kwargs)
    try:
        return pd.read_parquet(source, **kwargs)
    except ImportError as exc:
        raise RuntimeError(
            "Reading Parquet requires pyarrow or fastparquet. "
            "Install project dependencies with `python -m pip install -r requirements.txt`."
        ) from exc


def validate_roundtrip(
    original: pd.DataFrame,
    reloaded: pd.DataFrame,
    critical_columns: Iterable[str],
) -> dict[str, object]:
    """Confirm shape, columns, and critical dtypes survive a storage round trip.

    Returns an audit report when all checks pass and raises ``ValueError`` with
    a specific message when a mismatch is detected.
    """
    if original.shape != reloaded.shape:
        raise ValueError(f"Shape mismatch: {original.shape} != {reloaded.shape}")
    if original.columns.tolist() != reloaded.columns.tolist():
        raise ValueError("Column names or order changed during storage round trip.")

    requested = list(critical_columns)
    missing = [column for column in requested if column not in original.columns]
    if missing:
        raise ValueError(f"Critical columns are missing: {missing}")

    dtype_matches: dict[str, bool] = {}
    for column in requested:
        original_dtype = original[column].dtype
        reloaded_dtype = reloaded[column].dtype
        if pd.api.types.is_datetime64_any_dtype(original_dtype):
            matches = pd.api.types.is_datetime64_any_dtype(reloaded_dtype)
        elif pd.api.types.is_integer_dtype(original_dtype):
            matches = pd.api.types.is_integer_dtype(reloaded_dtype)
        elif pd.api.types.is_float_dtype(original_dtype):
            matches = pd.api.types.is_float_dtype(reloaded_dtype)
        elif pd.api.types.is_string_dtype(original_dtype):
            matches = pd.api.types.is_string_dtype(reloaded_dtype)
        else:
            matches = pd.api.types.is_dtype_equal(original_dtype, reloaded_dtype)
        dtype_matches[column] = bool(matches)
    if not all(dtype_matches.values()):
        raise ValueError(f"Critical dtype mismatch: {dtype_matches}")

    return {
        "valid": True,
        "shape_match": True,
        "columns_match": True,
        "critical_dtype_matches": dtype_matches,
    }
