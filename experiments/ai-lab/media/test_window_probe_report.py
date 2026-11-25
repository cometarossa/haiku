import unittest
from window_probe_report import analyze

def complete():
    lines=["INIT 20","START 100 1000100 1"]
    t=100
    for s in (1,2,3):
        for op,v in (("Title",1),("IsPlaying",1),("Position",s*1000)):
            lines.append(f"QUERY {s} 2 {op} {t} {t+10} 0 {v}")
            t+=20
    return "\n".join(lines+[f"END {t} 9 0"])

class ProbeReportTest(unittest.TestCase):
    def test_complete(self):
        r=analyze(complete(),[2])
        self.assertTrue(r["playback_valid"])
        self.assertEqual(r["by_operation"]["Title"]["median_us"],10)

    def test_failed_title(self):
        s="INIT 10\nSTART 100 1000100 1\nQUERY 1 2 Title 100 1000200 -1 0\nEND 1000300 1 1"
        r=analyze(s,[2])
        self.assertFalse(r["playback_valid"])
        self.assertEqual(r["not_attempted"],8)
        self.assertEqual(r["deadline_overrun_us"],200)

    def test_nonadvancing(self):
        self.assertFalse(analyze(complete().replace("0 3000","0 2000"),[2])["playback_valid"])

    def test_reject_bad_logs(self):
        for s in (complete().replace("END 280 9 0","END 280 8 0"),
                  complete().replace("QUERY 1 2 Title","QUERY 1 3 Title"),
                  complete().replace("QUERY 1 2 Title 100 110","QUERY 1 2 Title 100 90"),
                  "\n".join(complete().splitlines()[:-1])):
            with self.assertRaises(ValueError):analyze(s,[2])
