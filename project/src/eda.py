"""Reusable exploratory-data-analysis summaries for project dataframes."""

from __future__ import annotations

import numpy as np
import pandas as pd


def eda_summary(
    df: pd.DataFrame,
    *,
    missing_threshold: float = 0.20,
    dominance_threshold: float = 0.95,
) -> dict[str, object]:
    """Build reusable numeric, categorical, correlation, and quality summaries.

    Args:
        df: Dataframe to profile.
        missing_threshold: Fraction missing that triggers an attention flag.
        dominance_threshold: Largest-category share that triggers an attention
            flag for non-numeric columns.

    Returns:
        A dictionary containing ``overview``, ``numeric_summary``,
        ``categorical_profiles``, ``correlation``, and ``attention`` objects.
        This function does not mutate ``df``.
    """
    if df.empty:
        raise ValueError("EDA requires a non-empty dataframe.")
    if not 0 <= missing_threshold <= 1:
        raise ValueError("missing_threshold must be between 0 and 1.")
    if not 0 < dominance_threshold <= 1:
        raise ValueError("dominance_threshold must be greater than 0 and at most 1.")

    overview = pd.DataFrame(
        {
            "dtype": df.dtypes.astype(str),
            "non_null": df.notna().sum(),
            "missing": df.isna().sum(),
            "missing_pct": df.isna().mean(),
            "unique": df.nunique(dropna=True),
        }
    )

    numeric = df.select_dtypes(include="number")
    if numeric.empty:
        numeric_summary = pd.DataFrame()
        correlation = pd.DataFrame()
    else:
        numeric_summary = numeric.describe().T
        numeric_summary["median"] = numeric.median()
        numeric_summary["skew"] = numeric.skew()
        numeric_summary["kurtosis"] = numeric.kurt()
        correlation = numeric.corr()

    categorical_columns = df.select_dtypes(exclude="number").columns
    categorical_profiles = {
        column: df[column].value_counts(dropna=False).rename("count").to_frame()
        for column in categorical_columns
    }

    attention_rows: list[dict[str, object]] = []
    for column in df.columns:
        missing_pct = float(df[column].isna().mean())
        if missing_pct >= missing_threshold and missing_pct > 0:
            attention_rows.append(
                {"column": column, "issue": "high_missingness", "value": missing_pct}
            )

        non_missing = df[column].dropna()
        if non_missing.nunique() <= 1:
            attention_rows.append(
                {"column": column, "issue": "near_zero_variance", "value": 1.0}
            )
        elif not pd.api.types.is_numeric_dtype(df[column]):
            dominant_share = float(non_missing.value_counts(normalize=True).iloc[0])
            if dominant_share >= dominance_threshold:
                attention_rows.append(
                    {"column": column, "issue": "dominant_category", "value": dominant_share}
                )
        elif np.isclose(float(non_missing.std(ddof=0)), 0.0):
            attention_rows.append(
                {"column": column, "issue": "near_zero_variance", "value": 0.0}
            )

    attention = pd.DataFrame(attention_rows, columns=["column", "issue", "value"])
    return {
        "overview": overview,
        "numeric_summary": numeric_summary,
        "categorical_profiles": categorical_profiles,
        "correlation": correlation,
        "attention": attention,
    }
