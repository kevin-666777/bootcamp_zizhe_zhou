"""Modular DataFrame cleaning functions."""

from collections.abc import Sequence

import pandas as pd


def _resolve_columns(df: pd.DataFrame, columns: Sequence[str] | None) -> list[str]:
    """Return requested columns, or all numeric columns when omitted."""
    selected = list(columns) if columns is not None else list(df.select_dtypes(include="number").columns)
    missing = [column for column in selected if column not in df.columns]
    if missing:
        raise KeyError(f"Columns not found: {missing}")
    return selected


def fill_missing_median(
    df: pd.DataFrame,
    columns: Sequence[str] | None = None,
) -> pd.DataFrame:
    """Return a copy with missing numeric values filled by column medians.

    If ``columns`` is omitted, all numeric columns are selected. Requested
    columns must be numeric and must contain at least one non-missing value.
    """
    result = df.copy()
    selected = _resolve_columns(result, columns)
    non_numeric = [column for column in selected if not pd.api.types.is_numeric_dtype(result[column])]
    if non_numeric:
        raise TypeError(f"Median imputation requires numeric columns: {non_numeric}")

    for column in selected:
        median = result[column].median()
        if pd.isna(median):
            raise ValueError(f"Cannot calculate a median for all-missing column: {column}")
        result[column] = result[column].fillna(median)
    return result


def drop_missing(
    df: pd.DataFrame,
    threshold: float = 0.5,
) -> pd.DataFrame:
    """Return a copy without columns whose missing fraction exceeds ``threshold``.

    ``threshold`` is a proportion from 0 through 1. Columns exactly at the
    threshold are retained; only columns above it are removed.
    """
    if not 0 <= threshold <= 1:
        raise ValueError("threshold must be between 0 and 1")
    missing_fraction = df.isna().mean()
    keep_columns = missing_fraction[missing_fraction <= threshold].index
    return df.loc[:, keep_columns].copy()


def normalize_data(
    df: pd.DataFrame,
    columns: Sequence[str] | None = None,
) -> pd.DataFrame:
    """Return a copy with selected numeric columns min-max scaled to [0, 1].

    Constant columns are set to 0.0 because they contain no relative spread.
    Missing values remain missing, allowing imputation policy to stay explicit.
    """
    result = df.copy()
    selected = _resolve_columns(result, columns)
    non_numeric = [column for column in selected if not pd.api.types.is_numeric_dtype(result[column])]
    if non_numeric:
        raise TypeError(f"Normalization requires numeric columns: {non_numeric}")

    for column in selected:
        minimum = result[column].min()
        maximum = result[column].max()
        if pd.isna(minimum) or pd.isna(maximum):
            raise ValueError(f"Cannot normalize all-missing column: {column}")
        if maximum == minimum:
            result[column] = 0.0
        else:
            result[column] = (result[column] - minimum) / (maximum - minimum)
    return result
