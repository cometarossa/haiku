import unittest
from test_window_probe_report import complete
from window_progress_report import progress

class ProgressTest(unittest.TestCase):
    def test_bounds(self):
        r=progress(complete(),[2])
        self.assertEqual(r["measured_windows"],1)
        x=r["rows"][0]
        self.assertEqual(x["position_delta_us"],2000)
        self.assertEqual(x["wall_time_lower_us"],110)
        self.assertEqual(x["wall_time_upper_us"],130)
        self.assertLess(x["rate_lower"],x["rate_midpoint"])
        self.assertLess(x["rate_midpoint"],x["rate_upper"])
    def test_missing_playing(self):
        s=complete().replace("QUERY 2 2 IsPlaying 180 190 0 1","QUERY 2 2 IsPlaying 180 190 0 0")
        r=progress(s,[2])
        self.assertEqual(r["measured_windows"],0)
        self.assertIsNone(r["median_midpoint_rate"])
    def test_incomplete(self):
        s="INIT 10\nSTART 100 1000100 1\nQUERY 1 2 Title 100 1000200 -1 0\nEND 1000300 1 1"
        self.assertEqual(progress(s,[2])["measured_windows"],0)
