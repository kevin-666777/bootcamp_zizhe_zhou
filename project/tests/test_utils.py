"""Tests for reusable dataframe utilities."""

import unittest

import pandas as pd

from src.utils import clean_column_names, parse_date_column


class UtilsTests(unittest.TestCase):
    def test_clean_column_names_returns_copy(self) -> None:
        original = pd.DataFrame({" Trade Date ": ["2025-01-02"], "Adjusted Close": [243.85]})

        cleaned = clean_column_names(original)

        self.assertEqual(cleaned.columns.tolist(), ["trade_date", "adjusted_close"])
        self.assertEqual(original.columns.tolist(), [" Trade Date ", "Adjusted Close"])

    def test_clean_column_names_rejects_duplicates(self) -> None:
        frame = pd.DataFrame([[1, 2]], columns=["Close Price", "close-price"])

        with self.assertRaises(ValueError):
            clean_column_names(frame)

    def test_parse_date_column(self) -> None:
        frame = pd.DataFrame({"date": ["2025-01-02", "2025-01-03"]})

        parsed = parse_date_column(frame)

        self.assertTrue(pd.api.types.is_datetime64_any_dtype(parsed["date"]))
        self.assertFalse(pd.api.types.is_datetime64_any_dtype(frame["date"]))
        self.assertEqual(frame["date"].tolist(), ["2025-01-02", "2025-01-03"])

    def test_parse_date_column_requires_column(self) -> None:
        with self.assertRaises(KeyError):
            parse_date_column(pd.DataFrame({"value": [1]}))


if __name__ == "__main__":
    unittest.main()
