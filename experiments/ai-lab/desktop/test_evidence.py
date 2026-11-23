"""Validate independent fork app_server native guest evidence, stdlib only."""
import csv
from pathlib import Path
import unittest

EVIDENCE = Path(__file__).resolve().parents[1] / (
    "evidence/haiku-beta6-window-2026-11-23"
)


class WindowLifecycleEvidence(unittest.TestCase):
    def check_run(self, basename, batches, per_batch):
        with (EVIDENCE / (basename + ".csv")).open(newline="") as file:
            rows = list(csv.DictReader(file))
        self.assertEqual(len(rows), batches)
        self.assertEqual(list(rows[0].keys()),
                         ["batch", "created", "closed", "failed"])
        for number, row in enumerate(rows, start=1):
            with self.subTest(batch=number):
                self.assertEqual(int(row["batch"]), number)
                self.assertEqual(int(row["created"]), per_batch)
                self.assertEqual(int(row["closed"]), per_batch)
                self.assertEqual(int(row["failed"]), 0)
        stderr = (EVIDENCE / (basename + ".stderr")).read_text()
        self.assertIn("batches=%d windows_per_batch=%d" % (
            batches, per_batch), stderr)
        self.assertIn("completed=%d failures=0" % (
            batches * per_batch), stderr)

    def test_5_by_8(self):
        self.check_run("window_lifecycle_5x8", 5, 8)

    def test_20_by_10(self):
        self.check_run("window_lifecycle_20x10", 20, 10)


if __name__ == "__main__":
    unittest.main()
