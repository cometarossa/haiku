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


class MediaConcurrencyEvidence(unittest.TestCase):
    def _check(self, name: str, threads: int, cycles: int = 100) -> None:
        with (EVIDENCE / name).open(newline="", encoding="utf-8") as file:
            rows = list(csv.DictReader(file))
        self.assertEqual(len(rows), threads * cycles)
        for t in range(threads):
            for i in range(cycles):
                row = rows[t * cycles + i]
                with self.subTest(thread=t, iteration=i + 1):
                    self.assertEqual(int(row["thread"]), t)
                    self.assertEqual(int(row["iteration"]), i + 1)
                    self.assertEqual(int(row["init_status"]), 0)
                    self.assertEqual(int(row["tracks"]), 1)
                    self.assertEqual(int(row["first_track_status"]), 0)
        error_log = (EVIDENCE / name.replace(".csv", ".stderr")).read_text()
        self.assertIn("threads=%d" % threads, error_log)
        self.assertIn("cycles=%d failures=0" % (threads * cycles), error_log)

    def test_parallel_four_threads(self):
        self._check("media_parallel_4x100.csv", 4)

    def test_parallel_eight_threads(self):
        self._check("media_parallel_8x100.csv", 8)


if __name__ == "__main__":
    unittest.main()
