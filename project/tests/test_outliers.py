"""Tests for reusable outlier-analysis utilities."""

import unittest

import pandas as pd

from src.outliers import (
    detect_outliers_iqr,
    detect_outliers_zscore,
    flag_outliers,
    sensitivity_summary,
    winsorize_series,
)


class OutlierTests(unittest.TestCase):
    def test_iqr_flags_extreme_value_and_preserves_missing(self) -> None:
        values = pd.Series([1.0, 1.1, 0.9, 1.0, 10.0, None], index=list("abcdef"))
        flags = detect_outliers_iqr(values)

        self.assertTrue(flags.loc["e"])
        self.assertFalse(flags.loc["f"])
        self.assertEqual(flags.dtype, bool)

    def test_zscore_constant_series_has_no_flags(self) -> None:
        flags = detect_outliers_zscore(pd.Series([2.0, 2.0, 2.0]))
        self.assertFalse(flags.any())

    def test_winsorize_clips_both_tails_without_mutation(self) -> None:
        values = pd.Series([-100.0, 0.0, 1.0, 2.0, 100.0])
        result = winsorize_series(values, 0.2, 0.8)

        self.assertGreater(result.min(), values.min())
        self.assertLess(result.max(), values.max())
        self.assertEqual(values.iloc[0], -100.0)

    def test_flag_outliers_returns_copy(self) -> None:
        frame = pd.DataFrame({"return": [0.0, 0.01, -0.01, 0.5]})
        result = flag_outliers(frame, "return")

        self.assertIn("return_outlier_iqr", result.columns)
        self.assertNotIn("return_outlier_iqr", frame.columns)

    def test_sensitivity_has_three_treatments(self) -> None:
        values = pd.Series([0.0, 0.01, -0.01, 0.5])
        summary = sensitivity_summary(values, detect_outliers_iqr(values))

        self.assertEqual(summary.index.tolist(), ["all", "iqr_filtered", "winsorized_1_99"])
        self.assertLess(summary.loc["iqr_filtered", "count"], summary.loc["all", "count"])


if __name__ == "__main__":
    unittest.main()
