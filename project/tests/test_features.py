"""Tests for leakage-aware volatility features."""

import unittest

import numpy as np
import pandas as pd

from src.features import (
    MODEL_FEATURE_COLUMNS,
    TARGET_COLUMN,
    WEEKDAY_COLUMNS,
    build_volatility_features,
    make_modeling_table,
)


def sample_market_data(rows: int = 30) -> pd.DataFrame:
    dates = pd.bdate_range("2025-01-06", periods=rows)
    close = pd.Series(100 * np.cumprod(np.repeat(1.01, rows)))
    return pd.DataFrame(
        {
            "date": dates,
            "open": close * 0.995,
            "high": close * 1.01,
            "low": close * 0.99,
            "adj_close": close,
            "volume": np.arange(rows) * 1_000 + 1_000_000,
        }
    )


class FeatureTests(unittest.TestCase):
    def test_target_is_next_day_absolute_return(self) -> None:
        featured = build_volatility_features(sample_market_data())

        self.assertAlmostEqual(featured.loc[0, TARGET_COLUMN], 0.01)
        self.assertTrue(pd.isna(featured.iloc[-1][TARGET_COLUMN]))

    def test_weekday_encoding_has_exactly_one_active_day(self) -> None:
        featured = build_volatility_features(sample_market_data())

        self.assertTrue((featured[WEEKDAY_COLUMNS].sum(axis=1) == 1).all())
        self.assertTrue(all(str(featured[column].dtype) == "int8" for column in WEEKDAY_COLUMNS))

    def test_future_change_does_not_change_past_features(self) -> None:
        original = sample_market_data()
        revised = original.copy()
        revised.loc[25:, "adj_close"] *= 2

        first = build_volatility_features(original)
        second = build_volatility_features(revised)

        pd.testing.assert_frame_equal(
            first.loc[:23, MODEL_FEATURE_COLUMNS], second.loc[:23, MODEL_FEATURE_COLUMNS]
        )

    def test_modeling_table_removes_warmup_and_final_target(self) -> None:
        featured = build_volatility_features(sample_market_data())
        table = make_modeling_table(featured)

        self.assertFalse(table.isna().any().any())
        self.assertLess(len(table), len(featured))
        self.assertEqual(table.columns.tolist(), ["date", *MODEL_FEATURE_COLUMNS, TARGET_COLUMN])

    def test_unsorted_dates_are_rejected(self) -> None:
        frame = sample_market_data().iloc[::-1].reset_index(drop=True)

        with self.assertRaisesRegex(ValueError, "sorted"):
            build_volatility_features(frame)


if __name__ == "__main__":
    unittest.main()
