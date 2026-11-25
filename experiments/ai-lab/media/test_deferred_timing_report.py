import unittest
from deferred_timing_report import summarize_timing

D="LAB_VIDEO_DEFERRED queued=2 coalesced=1 failed=0 handled=2 cancelled=0 draw=1 skipped=1"
T="LAB_VIDEO_DEFERRED_TIMING queue_us=120 handler_us=52 bitmap_us=19 draw_us=20"

class DeferredTimingTest(unittest.TestCase):
    def test_valid(self):
        s=summarize_timing(D+"\n"+T,1)
        self.assertEqual(s["mean_queue_us"],60)
        self.assertEqual(s["mean_handler_us"],26)
        self.assertEqual(summarize_timing(D,0),{})
    def test_invalid(self):
        for log,n in ((T,1),(D+"\n"+T,2),(D+"\n"+T.replace("draw_us=20","draw_us=40"),1),(D+"\n"+T.replace("queue_us=120","queue_us=-1"),1)):
            with self.assertRaises(ValueError):
                summarize_timing(log,n)
