"""Tests for time-aware regression modeling."""

import unittest

import numpy as np
import pandas as pd

from src.modeling import (
    REGRESSION_FEATURE_COLUMNS,
    chronological_train_test_split,
    evaluate_holdout,
    expanding_window_backtest,
    regression_candidates,
    select_regression_model,
    standardized_coefficients,
)


def sample_modeling_data(rows: int = 100) -> pd.DataFrame:
    index = np.arange(rows, dtype=float)
    return pd.DataFrame(
        {
            "date": pd.bdate_range("2024-01-02", periods=rows),
            "signal": index / rows,
            "rolling_vol_21d": 0.01 + index / 10_000,
            "target": 0.005 + index / 5_000,
        }
    )


class ModelingTests(unittest.TestCase):
    def test_regression_features_use_friday_as_reference(self) -> None:
        self.assertNotIn("weekday_fri", REGRESSION_FEATURE_COLUMNS)
        self.assertIn("weekday_mon", REGRESSION_FEATURE_COLUMNS)

    def test_chronological_split_preserves_order(self) -> None:
        split = chronological_train_test_split(
            sample_modeling_data(), feature_columns=["signal", "rolling_vol_21d"],
            target_column="target", train_fraction=0.8
        )
        self.assertEqual(len(split.train), 80)
        self.assertEqual(len(split.test), 20)
        self.assertLess(split.train["date"].max(), split.test["date"].min())

    def test_unsorted_dates_are_rejected(self) -> None:
        data = sample_modeling_data().iloc[::-1].reset_index(drop=True)
        with self.assertRaisesRegex(ValueError, "sorted"):
            chronological_train_test_split(
                data, feature_columns=["signal", "rolling_vol_21d"], target_column="target"
            )

    def test_candidate_selection_refits_and_reports_metrics(self) -> None:
        data = sample_modeling_data()
        split = chronological_train_test_split(
            data, feature_columns=["signal", "rolling_vol_21d"], target_column="target"
        )
        name, model, comparison = select_regression_model(
            split.train, feature_columns=split.feature_columns, target_column="target"
        )
        self.assertIn(name, regression_candidates())
        self.assertEqual(set(comparison.columns), {"model", "mae", "rmse", "r2"})
        self.assertEqual(len(model.predict(split.test[list(split.feature_columns)])), len(split.test))

    def test_holdout_evaluation_uses_training_tail_threshold(self) -> None:
        split = chronological_train_test_split(
            sample_modeling_data(), feature_columns=["signal", "rolling_vol_21d"],
            target_column="target"
        )
        _, model, _ = select_regression_model(
            split.train, feature_columns=split.feature_columns, target_column="target"
        )
        summary, errors = evaluate_holdout(model, split)
        self.assertAlmostEqual(summary.loc[0, "tail_threshold"], split.train["target"].quantile(0.8))
        self.assertEqual(len(errors), len(split.test))
        self.assertTrue((errors["prediction"] >= 0).all())

    def test_standardized_coefficients_cover_features(self) -> None:
        split = chronological_train_test_split(
            sample_modeling_data(), feature_columns=["signal", "rolling_vol_21d"],
            target_column="target"
        )
        _, model, _ = select_regression_model(
            split.train, feature_columns=split.feature_columns, target_column="target"
        )
        coefficients = standardized_coefficients(model, split.feature_columns)
        self.assertEqual(set(coefficients["feature"]), set(split.feature_columns))

    def test_expanding_backtest_evaluates_each_future_row_once(self) -> None:
        data = sample_modeling_data(95)
        folds, predictions = expanding_window_backtest(
            data,
            feature_columns=["signal", "rolling_vol_21d"],
            target_column="target",
            initial_train_size=50,
            test_size=20,
        )
        self.assertEqual(folds["test_rows"].tolist(), [20, 20, 5])
        self.assertEqual(len(predictions), 45)
        self.assertFalse(predictions["date"].duplicated().any())
        self.assertEqual(predictions["date"].tolist(), data["date"].iloc[50:].tolist())

    def test_expanding_backtest_never_trains_on_test_dates(self) -> None:
        folds, _ = expanding_window_backtest(
            sample_modeling_data(80),
            feature_columns=["signal", "rolling_vol_21d"],
            target_column="target",
            initial_train_size=50,
            test_size=15,
        )
        self.assertTrue((folds["train_end"] < folds["test_start"]).all())
        self.assertEqual(folds["train_rows"].tolist(), [50, 65])

    def test_expanding_backtest_rejects_unsorted_dates(self) -> None:
        data = sample_modeling_data(80).iloc[::-1].reset_index(drop=True)
        with self.assertRaisesRegex(ValueError, "sorted"):
            expanding_window_backtest(
                data,
                feature_columns=["signal", "rolling_vol_21d"],
                target_column="target",
                initial_train_size=50,
            )


if __name__ == "__main__":
    unittest.main()
