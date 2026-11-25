import unittest
from v19_deferred_report import deferred_records,lifecycle

def pos(x):
    return f'Reply BMessage(B_REPLY):\n   "result" (B_INT64_TYPE) : {x} (0x0)\n'

class DeferredReportTest(unittest.TestCase):
    def test_valid(self):
        self.assertEqual(deferred_records("LAB_VIDEO_DEFERRED queued=4 coalesced=100 failed=1 handled=3 cancelled=1 draw=2 skipped=1")[0]["draw"],2)
        self.assertEqual(deferred_records("ordinary log"),[])
    def test_bad(self):
        for s in ("queued=4 coalesced=1 failed=0 handled=2 cancelled=0 draw=2 skipped=0",
                  "queued=4 coalesced=1 failed=0 handled=4 cancelled=0 draw=1 skipped=0",
                  "queued=4"):
            with self.assertRaises(ValueError):deferred_records("LAB_VIDEO_DEFERRED "+s)
    def test_lifecycle(self):
        a="STOP\nfalse\n"+pos(0)+"SEEK\nfalse\n"+pos(28000000)
        b="PAUSE\nfalse\n"+pos(33000000)+"PAUSE_LATER\n"+pos(33000000)
        self.assertEqual(lifecycle(a,b)["seek_us"],28000000)
        with self.assertRaises(ValueError):lifecycle(a,b.replace("false","true"))
        with self.assertRaises(ValueError):lifecycle(a.replace("28000000","30000000"),b)
        with self.assertRaises(ValueError):lifecycle(a,b.replace("33000000 (0x0)\n","35000000 (0x0)\n",1))
