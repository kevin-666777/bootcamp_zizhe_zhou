"""Reusable exploratory data analysis summaries."""

from io import StringIO

import pandas as pd


def eda_summary(
    df: pd.DataFrame,
    *,
    high_missing_threshold: float = 0.20,
    dominant_category_threshold: float = 0.90,
    near_zero_variance_threshold: float = 1e-8,
) -> dict:
    """Return a structured profile and flags for columns needing attention.

    The profile includes ``DataFrame.info()``, missing counts, numeric
    ``describe`` output with skew and kurtosis, and value-count tables for
    every categorical/text column. Attention flags identify high missingness,
    near-zero numeric variance, constant columns, and dominating categories.
    Datetime columns are treated as temporal rather than categorical.
    """
    if not isinstance(df, pd.DataFrame):
        raise TypeError("df must be a pandas DataFrame")
    if df.empty:
        raise ValueError("df must contain at least one row")
    if not 0 <= high_missing_threshold <= 1:
        raise ValueError("high_missing_threshold must be between 0 and 1")
    if not 0 < dominant_category_threshold <= 1:
        raise ValueError("dominant_category_threshold must be in (0, 1]")
    if near_zero_variance_threshold < 0:
        raise ValueError("near_zero_variance_threshold cannot be negative")

    info_buffer = StringIO()
    df.info(buf=info_buffer)
    missing_counts = df.isna().sum().rename("missing_count")
    missing_fraction = df.isna().mean().rename("missing_fraction")

    numeric_columns = list(df.select_dtypes(include="number").columns)
    if numeric_columns:
        numeric_profile = df[numeric_columns].describe().T
        numeric_profile["missing_count"] = missing_counts[numeric_columns]
        numeric_profile["missing_fraction"] = missing_fraction[numeric_columns]
        numeric_profile["skew"] = df[numeric_columns].skew()
        numeric_profile["kurtosis"] = df[numeric_columns].kurt()
    else:
        numeric_profile = pd.DataFrame()

    categorical_columns = list(
        df.select_dtypes(include=["object", "string", "category", "bool"]).columns
    )
    categorical_profiles = {
        column: df[column].value_counts(dropna=False).rename("count").to_frame()
        for column in categorical_columns
    }

    flags: list[dict] = []
    for column in df.columns:
        if missing_fraction[column] > high_missing_threshold:
            flags.append({"column": column, "issue": "high_missingness", "value": missing_fraction[column]})
        unique_count = df[column].nunique(dropna=True)
        if unique_count <= 1:
            flags.append({"column": column, "issue": "constant_or_empty", "value": unique_count})

    for column in numeric_columns:
        variance = df[column].var()
        if pd.notna(variance) and 0 < variance <= near_zero_variance_threshold:
            flags.append({"column": column, "issue": "near_zero_variance", "value": variance})

    for column in categorical_columns:
        non_missing = df[column].dropna()
        if not non_missing.empty:
            dominant_share = non_missing.value_counts(normalize=True).iloc[0]
            if dominant_share >= dominant_category_threshold:
                flags.append({"column": column, "issue": "dominant_category", "value": dominant_share})

    return {
        "shape": df.shape,
        "info": info_buffer.getvalue(),
        "missing": pd.concat([missing_counts, missing_fraction], axis=1),
        "numeric_profile": numeric_profile,
        "categorical_profiles": categorical_profiles,
        "attention_flags": pd.DataFrame(flags, columns=["column", "issue", "value"]),
    }
