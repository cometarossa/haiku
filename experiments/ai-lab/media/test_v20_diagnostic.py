import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from v18_probe_load_runner import v20_diagnostic_script
from v20_diagnostic_report import diagnostics
from test_proxy_video_stats_report import R
from test_deferred_timing_report import D,T


class V20DiagnosticTest(unittest.TestCase):
    def test_script(self):
        raw=Path(__file__).with_name("v18-probe-load-guest.sh").read_bytes()
        for n in (4,8,16):
            s=v20_diagnostic_script(raw,n)
            subprocess.run(["sh","-n"],input=s,check=True)
            order=" ".join(f"{n}-{state}" for state in ("off","on","on","off"))
            self.assertIn(f"for spec in {order};".encode(),s)
            self.assertIn(f"v20-diagnostic-{n}-ram".encode(),s)
            self.assertEqual(s.count(b'"$catchup" "$view" "$timing" "$proxy"'),2)
            for m,flag in (("timing","own_timing"),("proxy","own_proxy")):
                self.assertIn(f'(set -C; : > "${m}"); {flag}=1'.encode(),s)
                self.assertIn(f'rm -f "${m}"'.encode(),s)
        with self.assertRaises(ValueError):v20_diagnostic_script(raw,12)
    def test_real_shell_marker_cleanup_and_preflight(self):
        raw=Path(__file__).with_name("v18-probe-load-guest.sh").read_bytes()
        script=v20_diagnostic_script(raw,8).decode()
        prefix=script[script.index("stats=/boot/"):script.index("for f in stream-a.mp4")]
        setup=script[script.index('(set -C; : > "$preflight")'):script.index("run=0")]
        with tempfile.TemporaryDirectory() as d:
            prefix=prefix.replace("/boot/home/config/settings",d)
            subprocess.run(["sh","-ec",prefix+setup+"x=940; y=220; cleanup"],check=True)
            self.assertEqual(list(Path(d).iterdir()),[])
            marker=Path(d)/"haiku-lab-video-proxy-stats"
            marker.touch()
            rejected=subprocess.run(["sh","-ec",prefix+setup],capture_output=True)
            self.assertEqual(rejected.returncode,7)
            self.assertEqual(list(Path(d).iterdir()),[marker])

    @patch("v20_diagnostic_report.media_summary")
    @patch("v20_diagnostic_report.media_parse")
    def test_cross_check(self,parse,summary):
        summary.return_value={"producer":{"records":1,"fills":12,"fill_timeouts":5},"consumer":{"records":1}}
        self.assertEqual(diagnostics(R,1,"off")["proxy"]["timeouts"],5)
        self.assertEqual(diagnostics(R+"\n"+D+"\n"+T,1,"on")["timing"]["mean_queue_us"],60)
        with self.assertRaises(ValueError):diagnostics(R+"\n"+D+"\n"+T,1,"off")
        summary.return_value["producer"]["fill_timeouts"]=6
        with self.assertRaises(ValueError):diagnostics(R,1,"off")
