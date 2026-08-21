"""Summary helpers for the Python fundamentals homework."""

import pandas as pd


def get_summary_stats(df: pd.DataFrame) -> pd.DataFrame:
    """Return descriptive statistics for all numeric columns in ``df``."""
    return df.select_dtypes(include="number").describe()


def get_category_summary(
    df: pd.DataFrame,
    category_column: str = "category",
    value_column: str = "value",
) -> pd.DataFrame:
    """Aggregate count, mean, minimum, maximum, and sum by category."""
    return (
        df.groupby(category_column, as_index=False)
        .agg(
            count=(value_column, "count"),
            mean=(value_column, "mean"),
            minimum=(value_column, "min"),
            maximum=(value_column, "max"),
            total=(value_column, "sum"),
        )
        .sort_values(category_column)
        .reset_index(drop=True)
    )
