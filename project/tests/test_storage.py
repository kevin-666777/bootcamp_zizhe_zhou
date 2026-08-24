"""Tests for suffix-routed dataframe storage."""

import tempfile
import unittest
from pathlib import Path

import pandas as pd

from src.storage import read_df, validate_roundtrip, write_df


class StorageTests(unittest.TestCase):
    def setUp(self) -> None:
        self.frame = pd.DataFrame(
            {
                "date": pd.to_datetime(["2025-01-02", "2025-01-03"]),
                "close": [243.85, 245.0],
                "volume": pd.Series([50_000_000, 52_000_000], dtype="int64"),
            }
        )

    def test_csv_roundtrip_and_parent_creation(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "nested" / "sample.csv"
            write_df(self.frame, path, date_format="%Y-%m-%d")
            reloaded = read_df(path, parse_dates=["date"])

            report = validate_roundtrip(self.frame, reloaded, ["date", "volume"])
            self.assertTrue(report["valid"])

    def test_parquet_roundtrip(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "sample.parquet"
            write_df(self.frame, path)
            reloaded = read_df(path)

            report = validate_roundtrip(self.frame, reloaded, ["date", "close", "volume"])
            self.assertTrue(report["valid"])

    def test_read_missing_file_has_clear_error(self) -> None:
        with self.assertRaisesRegex(FileNotFoundError, "does not exist"):
            read_df("missing.csv")

    def test_roundtrip_rejects_datetime_as_text(self) -> None:
        text_dates = self.frame.assign(date=self.frame["date"].dt.strftime("%Y-%m-%d"))

        with self.assertRaisesRegex(ValueError, "dtype mismatch"):
            validate_roundtrip(self.frame, text_dates, ["date"])

    def test_unsupported_suffix_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            with self.assertRaisesRegex(ValueError, "Unsupported"):
                write_df(self.frame, Path(directory) / "sample.json")


if __name__ == "__main__":
    unittest.main()
