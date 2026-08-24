"""General-purpose dataframe utilities used across project stages."""

from __future__ import annotations

import re

import pandas as pd


def clean_column_names(df: pd.DataFrame) -> pd.DataFrame:
    """Return a copy with predictable snake_case column names.

    Leading and trailing whitespace is removed, text is lowercased, and each
    run of non-alphanumeric characters is replaced by one underscore. This is
    useful after ingestion because market-data vendors often use inconsistent
    labels such as ``Adjusted Close`` or ``trade-volume``.

    Args:
        df: Source dataframe. It is not modified in place.

    Returns:
        A dataframe copy with cleaned, unique column names.

    Raises:
        ValueError: If cleaning would create duplicate column names.
    """
    cleaned = [
        re.sub(r"[^a-z0-9]+", "_", str(column).strip().lower()).strip("_")
        for column in df.columns
    ]
    if any(not column for column in cleaned):
        raise ValueError("Column names must contain at least one letter or number.")
    if len(set(cleaned)) != len(cleaned):
        raise ValueError("Column-name cleaning produced duplicate names.")

    result = df.copy()
    result.columns = cleaned
    return result


def parse_date_column(
    df: pd.DataFrame,
    column: str = "date",
    *,
    errors: str = "raise",
    utc: bool = False,
) -> pd.DataFrame:
    """Return a copy with one column converted to pandas datetime values.

    Args:
        df: Source dataframe. It is not modified in place.
        column: Column to parse.
        errors: Invalid-value behavior passed to :func:`pandas.to_datetime`.
        utc: Whether parsed timestamps should be timezone-aware UTC values.

    Returns:
        A dataframe copy whose requested column has a datetime dtype.

    Raises:
        KeyError: If ``column`` is not present.
    """
    if column not in df.columns:
        raise KeyError(f"Date column {column!r} was not found.")

    result = df.copy()
    result[column] = pd.to_datetime(result[column], errors=errors, utc=utc)
    return result
