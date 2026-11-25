import unittest
from video_view_stats_report import parse, summarize

R = ("LAB_VIDEO_VIEW calls=6 null=1 looper_fail=1 bitmap_fail=1 overlay=1 "
     "invalidate=1 draw=1 total_us=20200 update_us=18 looper_us=25 "
     "bitmap_us=28 overlay_us=20021 invalidate_us=24 draw_us=19")


class ViewReportTest(unittest.TestCase):
    def test_valid(self):
        v=summarize(parse("other log\n"+R+"\n"+R),2)
        self.assertEqual(v["calls"],12)
        self.assertEqual(v["records"],2)
        self.assertEqual(v["unattributed_us"],130)

    def test_off(self):
        self.assertEqual(summarize(parse("other log"),4,False),{})
        with self.assertRaises(ValueError):
            summarize(parse(R),1,False)

    def test_wrong_count(self):
        with self.assertRaises(ValueError):
            summarize(parse(R),2)

    def test_invalid(self):
        for text in (R.replace("calls=6","calls=7"),
                     R.replace("total_us=20200","total_us=20000"),
                     R.replace("draw=1","draw=-1"),
                     R.replace("draw=1","null=1"),
                     R.replace("draw=1","draw=0").replace("calls=6","calls=5"),
                     "interleaved "+R,
                     R+" more output"):
            with self.subTest(text=text), self.assertRaises(ValueError):
                parse(text)
