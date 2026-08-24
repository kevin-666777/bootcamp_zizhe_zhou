"""Offline tests for market-data validation and snapshot naming."""

import tempfile
import unittest
from pathlib import Path

import pandas as pd

from src.ingestion import save_raw_snapshot, validate_daily_ohlcv


def sample_ohlcv() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "date": pd.to_datetime(["2025-01-02", "2025-01-03"]),
            "open": [242.0, 243.0],
            "high": [245.0, 246.0],
            "low": [241.0, 242.0],
            "close": [244.0, 245.0],
            "adj_close": [243.7, 244.7],
            "volume": [50_000_000, 52_000_000],
            "symbol": ["AAPL", "AAPL"],
            "source": ["test", "test"],
        }
    )


class IngestionTests(unittest.TestCase):
    def test_validation_report(self) -> None:
        report = validate_daily_ohlcv(sample_ohlcv())

        self.assertTrue(report["valid"])
        self.assertEqual(report["shape"], (2, 9))
        self.assertEqual(report["date_min"], "2025-01-02")

    def test_validation_rejects_impossible_high(self) -> None:
        frame = sample_ohlcv()
        frame.loc[0, "high"] = 240.0

        with self.assertRaises(ValueError):
            validate_daily_ohlcv(frame)

    def test_snapshot_has_reproducible_name(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = save_raw_snapshot(sample_ohlcv(), directory, "AAPL")

            self.assertEqual(path.name, "aapl_ohlcv_20250102_20250103.csv")
            self.assertTrue(Path(path).is_file())


if __name__ == "__main__":
    unittest.main()
