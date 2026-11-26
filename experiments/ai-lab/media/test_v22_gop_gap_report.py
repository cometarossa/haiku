import unittest
from proxy_video_stats_report import parse
from v22_gop_gap_report import gap_metrics
from test_proxy_video_stats_report import R


class GapSeverityTest(unittest.TestCase):
    def test_rejected(self):
        result=gap_metrics(parse(R),1)
        self.assertEqual(result["timeout_fraction"],.3)
        self.assertEqual(result["mean_gap_when_rejected"],10)
        self.assertEqual(result["max_gap_when_rejected"],12)
        self.assertEqual(result["gap_frames_per_call"],3)
        self.assertEqual(result["affected_tracks"],1)

    def test_no_rejections(self):
        record="LAB_VIDEO_PROXY calls=10 cached=0 gap_timeout=0 seek_timeout=0 read_timeout=0 other_errors=0 success=10 gap_frames=0 max_gap=0"
        result=gap_metrics(parse(record),1)
        self.assertEqual(result["timeout_fraction"],0)
        self.assertIsNone(result["mean_gap_when_rejected"])
        self.assertIsNone(result["max_gap_when_rejected"])
        self.assertEqual(result["gap_frames_per_call"],0)

    def test_empty_track(self):
        record="LAB_VIDEO_PROXY calls=0 cached=0 gap_timeout=0 seek_timeout=0 read_timeout=0 other_errors=0 success=0 gap_frames=0 max_gap=0"
        with self.assertRaises(ValueError):
            gap_metrics(parse(record),1)
