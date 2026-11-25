import unittest
from proxy_video_stats_report import parse,summarize

R="LAB_VIDEO_PROXY calls=10 cached=1 gap_timeout=3 seek_timeout=1 read_timeout=1 other_errors=1 success=3 gap_frames=30 max_gap=12"

class ProxyReportTest(unittest.TestCase):
    def test_valid(self):
        s=summarize(parse(R+"\n"+R),2)
        self.assertEqual(s["timeouts"],10)
        self.assertEqual(s["max_gap"],12)
        self.assertEqual(summarize(parse("ordinary"),0),{})
    def test_bad(self):
        for s in (R.replace("calls=10","calls=11"),R.replace("gap_frames=30","gap_frames=12"),R.replace("max_gap=12","max_gap=5"),R.replace("gap_timeout=3","gap_timeout=-1"),"prefix "+R):
            with self.assertRaises(ValueError):parse(s)
        with self.assertRaises(ValueError):summarize(parse(R),2)
