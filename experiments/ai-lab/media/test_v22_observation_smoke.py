import subprocess
import tempfile
import unittest
from pathlib import Path
from v18_probe_load_runner import observation_script,record_teardown_clocks,v21_combined_script

class ObservationScriptTest(unittest.TestCase):
    def test_markers(self):
        raw=Path(__file__).with_name("v18-probe-load-guest.sh").read_bytes()
        for mode in ("off","on"):
            script=observation_script(record_teardown_clocks(v21_combined_script(raw,4)),mode).decode()
            subprocess.run(["sh","-n"],input=script,text=True,check=True)
            prefix=script[script.index("stats=/boot/"):script.index("for f in stream-a.mp4")]
            setup=script[script.index('(set -C; : > "$preflight")'):script.index("run=0")]
            with tempfile.TemporaryDirectory() as d:
                prefix=prefix.replace("/boot/home/config/settings",d)
                check='test -f "$observation"; test -f "$filltiming"; ' if mode=="on" else 'test ! -e "$observation"; test ! -e "$filltiming"; '
                subprocess.run(["sh","-ec",prefix+setup+check+'cleanup'],check=True)
                self.assertEqual(list(Path(d).iterdir()),[])
                marker=Path(d)/"haiku-lab-video-observation"
                marker.touch()
                r=subprocess.run(["sh","-ec",prefix+setup],capture_output=True)
                self.assertEqual(r.returncode,7)
                self.assertEqual(list(Path(d).iterdir()),[marker])
