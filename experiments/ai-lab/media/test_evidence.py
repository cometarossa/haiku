"""Validate AI-assisted fork-only Media Kit guest CSV artifacts (stdlib only)."""
import csv
from pathlib import Path
import unittest

EVIDENCE = Path(__file__).resolve().parent.parent / "evidence" / "haiku-beta6-2026-11-23"
FIELDS = [
    "iteration", "init_status", "tracks",
    "first_track_status", "elapsed_us",
]


class MediaLifecycleEvidence(unittest.TestCase):
    def _check(self, name: str, count: int) -> None:
        with (EVIDENCE / name).open(newline="", encoding="utf-8") as file:
            rows = list(csv.DictReader(file))
        self.assertEqual(len(rows), count)
        self.assertEqual(list(rows[0].keys()), FIELDS)
        for expected, row in enumerate(rows, start=1):
            with self.subTest(name=name, iteration=expected):
                self.assertEqual(int(row["iteration"]), expected)
                self.assertEqual(int(row["init_status"]), 0)
                self.assertEqual(int(row["tracks"]), 1)
                self.assertEqual(int(row["first_track_status"]), 0)
                self.assertGreaterEqual(int(row["elapsed_us"]), 0)

    def test_hundred_cycles(self):
        self._check("media_lifecycle.csv", 100)
        self.assertIn("iterations=100 failures=0",
            (EVIDENCE / "media_lifecycle.stderr").read_text())

    def test_thousand_cycles(self):
        self._check("media_lifecycle_1000.csv", 1000)
        self.assertIn("iterations=1000 failures=0",
            (EVIDENCE / "media_lifecycle_1000.stderr").read_text())


if __name__ == "__main__":
    unittest.main()
