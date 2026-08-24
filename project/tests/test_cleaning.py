"""Tests for market-data preprocessing."""

import unittest

import pandas as pd

from src.cleaning import clean_daily_ohlcv, cleaning_report, drop_missing


def dirty_ohlcv() -> pd.DataFrame:
    return pd.DataFrame(
        {
            " Date ": ["2025-01-03", "2025-01-02", "2025-01-02", "bad-date"],
            "Open": [243.0, 242.0, 242.5, 240.0],
            "High": [246.0, 245.0, 245.5, 241.0],
            "Low": [242.0, 241.0, 241.5, 239.0],
            "Close": [245.0, 244.0, 244.5, None],
            "Adj Close": [244.7, 243.7, 244.2, 239.5],
            "Volume": [52_000_000, 50_000_000, 51_000_000, 49_000_000],
            "Symbol": [" AAPL "] * 4,
            "Source": [" test "] * 4,
        }
    )


class CleaningTests(unittest.TestCase):
    def test_cleaning_sorts_deduplicates_and_parses(self) -> None:
        original = dirty_ohlcv()

        cleaned = clean_daily_ohlcv(original)

        self.assertEqual(len(cleaned), 2)
        self.assertEqual(cleaned["date"].dt.strftime("%Y-%m-%d").tolist(), ["2025-01-02", "2025-01-03"])
        self.assertEqual(cleaned.loc[0, "close"], 244.5)
        self.assertEqual(cleaned["symbol"].tolist(), ["AAPL", "AAPL"])
        self.assertEqual(original.columns[0], " Date ")

    def test_cleaning_drops_invalid_market_rule(self) -> None:
        frame = dirty_ohlcv().iloc[:2].copy()
        frame.loc[frame.index[0], "High"] = 240.0

        cleaned = clean_daily_ohlcv(frame)

        self.assertEqual(len(cleaned), 1)

    def test_drop_missing_requires_named_columns(self) -> None:
        with self.assertRaises(KeyError):
            drop_missing(pd.DataFrame({"close": [1.0]}), ["date", "close"])

    def test_cleaning_report_compares_rows(self) -> None:
        original = dirty_ohlcv()
        cleaned = clean_daily_ohlcv(original)

        report = cleaning_report(original, cleaned)

        self.assertEqual(report["rows_before"], 4)
        self.assertEqual(report["rows_after"], 2)
        self.assertEqual(report["duplicate_dates_before"], 1)


if __name__ == "__main__":
    unittest.main()
