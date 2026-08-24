"""Tests for the reusable EDA summary helper."""

import unittest

import pandas as pd

from src.eda import eda_summary


class EdaTests(unittest.TestCase):
    def setUp(self) -> None:
        self.frame = pd.DataFrame(
            {
                "value": [1.0, 2.0, 4.0, None],
                "constant": [1, 1, 1, 1],
                "category": ["A", "A", "A", "B"],
                "mostly_missing": [None, None, None, "known"],
            }
        )

    def test_summary_contains_required_sections(self) -> None:
        result = eda_summary(self.frame)

        self.assertEqual(
            set(result),
            {"overview", "numeric_summary", "categorical_profiles", "correlation", "attention"},
        )
        self.assertIn("skew", result["numeric_summary"].columns)
        self.assertIn("category", result["categorical_profiles"])

    def test_attention_flags_missingness_and_constant(self) -> None:
        attention = eda_summary(self.frame)["attention"]
        issues = set(map(tuple, attention[["column", "issue"]].to_numpy()))

        self.assertIn(("mostly_missing", "high_missingness"), issues)
        self.assertIn(("constant", "near_zero_variance"), issues)

    def test_summary_does_not_mutate_input(self) -> None:
        original = self.frame.copy(deep=True)
        eda_summary(self.frame)
        pd.testing.assert_frame_equal(self.frame, original)

    def test_empty_dataframe_is_rejected(self) -> None:
        with self.assertRaises(ValueError):
            eda_summary(pd.DataFrame())


if __name__ == "__main__":
    unittest.main()
