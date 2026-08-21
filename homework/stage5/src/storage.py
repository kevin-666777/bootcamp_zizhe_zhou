"""Suffix-routed pandas DataFrame storage helpers."""

from pathlib import Path
from typing import Union

import pandas as pd


PathLike = Union[str, Path]
PARQUET_SUFFIXES = {".parquet", ".pq", ".parq"}


def detect_format(path: PathLike) -> str:
    """Return ``csv`` or ``parquet`` based on a path's suffix."""
    suffix = Path(path).suffix.lower()
    if suffix == ".csv":
        return "csv"
    if suffix in PARQUET_SUFFIXES:
        return "parquet"
    raise ValueError(
        f"Unsupported file suffix '{suffix or '<none>'}'. "
        "Use .csv, .parquet, .pq, or .parq."
    )


def _parquet_error(action: str) -> RuntimeError:
    return RuntimeError(
        f"Cannot {action} Parquet because no compatible engine is available. "
        "Install one with `pip install pyarrow` or `pip install fastparquet`."
    )


def write_df(df: pd.DataFrame, path: PathLike) -> Path:
    """Write ``df`` as CSV or Parquet, creating parent directories."""
    destination = Path(path)
    destination.parent.mkdir(parents=True, exist_ok=True)
    file_format = detect_format(destination)

    if file_format == "csv":
        df.to_csv(destination, index=False)
    else:
        try:
            df.to_parquet(destination, index=False)
        except ImportError as error:
            raise _parquet_error("write") from error
    return destination


def read_df(path: PathLike) -> pd.DataFrame:
    """Read a CSV or Parquet file selected by suffix."""
    source = Path(path)
    if not source.exists():
        raise FileNotFoundError(f"Data file does not exist: {source}")
    file_format = detect_format(source)

    if file_format == "csv":
        columns = pd.read_csv(source, nrows=0).columns
        date_columns = [
            column
            for column in columns
            if column.lower() in {"date", "datetime", "timestamp"}
        ]
        return pd.read_csv(source, parse_dates=date_columns or None)

    try:
        return pd.read_parquet(source)
    except ImportError as error:
        raise _parquet_error("read") from error
