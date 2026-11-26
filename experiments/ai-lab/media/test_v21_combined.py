import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from v18_probe_load_runner import v21_combined_script
from v21_load_report import report
from v21_paired_summary import metrics
from test_v21_paired_summary import row


class CombinedTest(unittest.TestCase):
    def test_markers(self):
        raw=Path(__file__).with_name("v18-probe-load-guest.sh").read_bytes()
        for n in (4,8,16):
            s=v21_combined_script(raw,n).decode()
            subprocess.run(["sh","-n"],input=s,text=True,check=True)
            self.assertIn(f"for spec in {n}-off {n}-on {n}-on {n}-off;",s)
            self.assertIn("catchup=/boot/home/config/settings/haiku-lab-video-deferred",s)
            self.assertIn("single=/boot/home/config/settings/haiku-lab-h264-single-thread",s)
            prefix=s[s.index("stats=/boot/"):s.index("for f in stream-a.mp4")]
            setup=s[s.index('(set -C; : > "$preflight")'):s.index("run=0")]
            with tempfile.TemporaryDirectory() as d:
                prefix=prefix.replace("/boot/home/config/settings",d)
                check='test -f "$single"; test -f "$timing"; test ! -e "$catchup"; '
                subprocess.run(["sh","-ec",prefix+setup+check+'(set -C; : > "$catchup"); c=1; x=100; cleanup'],check=True)
                self.assertEqual(list(Path(d).iterdir()),[])
                marker=Path(d)/"haiku-lab-h264-single-thread"
                marker.touch()
                r=subprocess.run(["sh","-ec",prefix+setup],capture_output=True)
                self.assertEqual(r.returncode,7)
                self.assertEqual(list(Path(d).iterdir()),[marker])
    @patch("v21_load_report.diagnostics")
    @patch("v21_load_report.threads")
    @patch("v21_load_report.report_trial")
    def test_report(self,trial,threads,diag):
        trial.return_value={"player_exit":0,"valid":True}
        threads.return_value=[{}]*4
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)
            (p/"revision.txt").write_text("ai_2f9d27bf")
            for i,state in enumerate(("off","on","on","off")):
                for ext in ("exit","stderr"):
                    (p/f"{i:02d}-n4-{state}.{ext}").touch()
            (p/"done.txt").write_text("0")
            self.assertTrue(report(p,4,combined=True)["all_diagnostic_valid"])
            self.assertEqual([c.args[1] for c in threads.call_args_list],["on"]*4)
            self.assertEqual([c.kwargs["view_state"] for c in trial.call_args_list],["off","on","on","off"])
            self.assertEqual([c.args[2] for c in diag.call_args_list],["off","on","on","off"])
    def test_draw_count(self):
        r=row("on")
        r["deferred"]=[{"draw":40},{"draw":30}]
        self.assertEqual(metrics(r)["draw_submissions"],170)
