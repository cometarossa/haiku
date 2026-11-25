import subprocess
import unittest
from pathlib import Path
from v18_probe_load_runner import deferred_load_script
from v19_deferred_load_report import trials,view_treatment
from test_video_view_stats_report import R

class DeferredLoadTest(unittest.TestCase):
    def test_script(self):
        p=Path(__file__).with_name("v18-probe-load-guest.sh")
        for sixteen in (False,True):
            s=deferred_load_script(p.read_bytes(),sixteen)
            subprocess.run(["sh","-n"],input=s,check=True)
            order=" ".join(f"{n}-{state}" for n,state in trials(sixteen))
            self.assertIn(f"for spec in {order};".encode(),s)
            self.assertIn(b'catchup=/boot/home/config/settings/haiku-lab-video-deferred',s)
            self.assertIn(b'(set -C; : > "$view"); v=1',s)
            self.assertIn(b'20000000',s)
            self.assertEqual(s.count(b'"$catchup" "$view"'),2)
        with self.assertRaises(ValueError):
            deferred_load_script(b"wrong source")
    def test_treatment(self):
        off=R+" deferred=0"
        on=R.replace("calls=6","calls=10")+" deferred=4"
        d="LAB_VIDEO_DEFERRED queued=3 coalesced=1 failed=0 handled=3 cancelled=0 draw=3 skipped=0"
        self.assertEqual(view_treatment(off,1,"off")[0]["deferred"],0)
        self.assertEqual(view_treatment(on+"\n"+d,1,"on")[0]["deferred"],4)
        for log,n,state in ((on,1,"off"),(off,1,"on"),(on+"\n"+d,2,"on"),
                             (on+"\n"+d.replace("coalesced=1","coalesced=0"),1,"on")):
            with self.assertRaises(ValueError):
                view_treatment(log,n,state)
