"""Tests for Stage 11 evaluation helpers."""

import unittest

import numpy as np
from sklearn.metrics import mean_absolute_error

from src.evaluation import (
    bootstrap_metric,
    gaussian_mean_ci,
    moving_block_bootstrap_metric,
    percentile_ci,
)


class EvaluationTests(unittest.TestCase):
    def setUp(self) -> None:
        self.actual = np.array([1.0, 2.0, 3.0, 5.0, 8.0])
        self.predicted = np.array([1.2, 1.8, 2.5, 5.5, 7.0])

    def test_bootstrap_is_reproducible(self) -> None:
        first = bootstrap_metric(
            self.actual, self.predicted, mean_absolute_error, n_boot=500, random_state=11
        )
        second = bootstrap_metric(
            self.actual, self.predicted, mean_absolute_error, n_boot=500, random_state=11
        )
        np.testing.assert_array_equal(first, second)

    def test_block_bootstrap_returns_requested_count(self) -> None:
        estimates = moving_block_bootstrap_metric(
            self.actual,
            self.predicted,
            mean_absolute_error,
            block_size=2,
            n_boot=500,
        )
        self.assertEqual(estimates.shape, (500,))

    def test_intervals_are_ordered(self) -> None:
        gaussian = gaussian_mean_ci(np.abs(self.actual - self.predicted))
        bootstrap = percentile_ci(np.linspace(0.1, 0.9, 500))
        self.assertLess(gaussian[0], gaussian[1])
        self.assertLess(bootstrap[0], bootstrap[1])

    def test_too_few_bootstraps_are_rejected(self) -> None:
        with self.assertRaises(ValueError):
            bootstrap_metric(
                self.actual, self.predicted, mean_absolute_error, n_boot=100
            )


if __name__ == "__main__":
    unittest.main()
