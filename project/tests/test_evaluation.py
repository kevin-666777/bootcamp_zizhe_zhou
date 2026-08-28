"""Tests for uncertainty and scenario evaluation helpers."""

import unittest

import numpy as np
import pandas as pd

from src.evaluation import (
    bootstrap_mean_interval,
    compare_error_intervals,
    gaussian_mean_interval,
    subgroup_error_summary,
)


def sample_predictions() -> pd.DataFrame:
    actual = np.array([0.01, 0.02, 0.03, 0.04, 0.05, 0.06])
    prediction = np.array([0.01, 0.018, 0.025, 0.035, 0.04, 0.045])
    baseline = np.array([0.015, 0.025, 0.035, 0.045, 0.055, 0.065])
    return pd.DataFrame(
        {
            "group": ["A", "A", "A", "B", "B", "B"],
            "actual": actual,
            "prediction": prediction,
            "baseline": baseline,
            "absolute_error": np.abs(actual - prediction),
            "baseline_absolute_error": np.abs(actual - baseline),
        }
    )


class EvaluationTests(unittest.TestCase):
    def test_gaussian_interval_contains_sample_mean(self) -> None:
        estimate, lower, upper = gaussian_mean_interval([1, 2, 3, 4])
        self.assertEqual(estimate, 2.5)
        self.assertLess(lower, estimate)
        self.assertGreater(upper, estimate)

    def test_bootstrap_interval_is_reproducible(self) -> None:
        first = bootstrap_mean_interval([1, 2, 3, 4, 5], n_bootstrap=500, random_state=7)
        second = bootstrap_mean_interval([1, 2, 3, 4, 5], n_bootstrap=500, random_state=7)
        self.assertEqual(first, second)

    def test_moving_block_constant_values_have_zero_width(self) -> None:
        estimate, lower, upper = bootstrap_mean_interval(
            np.repeat(-0.01, 30), n_bootstrap=200, method="moving_block", block_size=5
        )
        self.assertAlmostEqual(estimate, -0.01)
        self.assertAlmostEqual(lower, -0.01)
        self.assertAlmostEqual(upper, -0.01)

    def test_invalid_block_size_is_rejected(self) -> None:
        with self.assertRaisesRegex(ValueError, "block_size"):
            bootstrap_mean_interval([1, 2, 3], method="moving_block", block_size=4)

    def test_interval_comparison_covers_each_scenario_and_method(self) -> None:
        predictions = sample_predictions()
        intervals = compare_error_intervals(
            predictions,
            {"All": np.repeat(True, 6), "Group B": predictions["group"].eq("B")},
            n_bootstrap=200,
            block_size=2,
        )
        self.assertEqual(len(intervals), 6)
        self.assertEqual(set(intervals["scenario"]), {"All", "Group B"})
        self.assertEqual(intervals.groupby("scenario")["method"].nunique().tolist(), [3, 3])

    def test_interval_comparison_rejects_mask_length_mismatch(self) -> None:
        with self.assertRaisesRegex(ValueError, "length"):
            compare_error_intervals(sample_predictions(), {"Bad": [True, False]})

    def test_subgroup_summary_reports_paired_improvement(self) -> None:
        summary = subgroup_error_summary(sample_predictions(), "group")
        self.assertEqual(summary["observations"].tolist(), [3, 3])
        self.assertTrue(np.allclose(summary["mae_difference"], summary["model_mae"] - summary["baseline_mae"]))


if __name__ == "__main__":
    unittest.main()
