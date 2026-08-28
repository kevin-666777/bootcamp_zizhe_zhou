"""Tests for stakeholder report generation."""

import tempfile
import unittest
from pathlib import Path

from src.delivery import build_stakeholder_report


class DeliveryTests(unittest.TestCase):
    def test_build_stakeholder_report_creates_multipage_pdf(self) -> None:
        project_root = Path(__file__).resolve().parents[1]
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "stakeholder_report.pdf"
            result = build_stakeholder_report(project_root, output)
            self.assertEqual(result, output.resolve())
            self.assertTrue(output.read_bytes().startswith(b"%PDF"))
            self.assertGreater(output.stat().st_size, 50_000)

    def test_missing_report_inputs_are_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            with self.assertRaisesRegex(FileNotFoundError, "inputs are missing"):
                build_stakeholder_report(directory)


if __name__ == "__main__":
    unittest.main()
