import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from v18_probe_load_runner import v22_gop_script
from v21_load_report import report
from v22_gop_decode_report import HASHES


class GopLoadTest(unittest.TestCase):
    def test_script(self):
        raw=Path(__file__).with_name("v18-probe-load-guest.sh").read_bytes()
        for n in (4,8,16):
            s=v22_gop_script(raw,n).decode()
            subprocess.run(["sh","-n"],input=s,text=True,check=True)
            self.assertIn(f"for spec in {n}-off {n}-on {n}-on {n}-off;",s)
            self.assertIn('fixture=gop-15.mp4; else fixture=gop-120.mp4',s)
            self.assertIn('cp "$fixture" "$tag-$i.mp4"; cmp "$fixture"',s)
            self.assertNotIn(': > "$catchup"',s)
            self.assertNotIn(': > "$timing"',s)
            self.assertIn('for f in gop-120.mp4 gop-15.mp4 media-window-probe SHA256SUMS;',s)
            prefix=s[s.index("stats=/boot/"):s.index("for f in gop-120.mp4")]
            setup=s[s.index('(set -C; : > "$preflight")'):s.index("run=0")]
            with tempfile.TemporaryDirectory() as d:
                prefix=prefix.replace("/boot/home/config/settings",d)
                subprocess.run(["sh","-ec",prefix+setup+'test -f "$single"; test ! -e "$catchup"; test ! -e "$timing"; x=100; cleanup'],check=True)
                self.assertEqual(list(Path(d).iterdir()),[])
    @patch("v21_load_report.diagnostics")
    @patch("v21_load_report.threads")
    @patch("v21_load_report.report_trial")
    def test_report(self,trial,threads,diag):
        trial.side_effect=lambda *a,**kw: {"player_exit":0,"valid":True}
        threads.return_value=[{}]*4
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)
            (p/"revision.txt").write_text("ai_2f9d27bf")
            (p/"input-sha256.txt").write_text("".join(f"{h}  gop-{g}.mp4\n" for g,h in HASHES.items()))
            for i,state in enumerate(("off","on","on","off")):
                for ext in ("exit","stderr"):
                    (p/f"{i:02d}-n4-{state}.{ext}").touch()
            (p/"done.txt").write_text("0")
            r=report(p,4,gop=True)
            self.assertTrue(r["all_diagnostic_valid"])
            self.assertEqual([x["gop"] for x in r["rows"]],[120,15,15,120])
            self.assertEqual([c.args[1] for c in threads.call_args_list],["on"]*4)
            self.assertEqual([c.kwargs["view_state"] for c in trial.call_args_list],["off"]*4)
            (p/"input-sha256.txt").write_text("wrong")
            with self.assertRaises(ValueError):report(p,4,gop=True)
