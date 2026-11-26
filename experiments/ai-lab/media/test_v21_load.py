import subprocess
import tempfile
import unittest
from pathlib import Path
from v18_probe_load_runner import v21_load_script

class ThreadLoadTest(unittest.TestCase):
    def test_script(self):
        raw=Path(__file__).with_name("v18-probe-load-guest.sh").read_bytes()
        for n in (4,8,16):
            s=v21_load_script(raw,n)
            subprocess.run(["sh","-n"],input=s,check=True)
            self.assertIn(f"for spec in {n}-off {n}-on {n}-on {n}-off;".encode(),s)
            self.assertIn(b"catchup=/boot/home/config/settings/haiku-lab-h264-single-thread",s)
            self.assertIn(b"deferred=/boot/home/config/settings/haiku-lab-video-deferred",s)
            self.assertNotIn(b': > "$timing"',s)
            self.assertNotIn(b': > "$deferred"',s)
            self.assertEqual(s.count(b'"$threadstats" "$deferred"'),2)
    def test_cleanup(self):
        raw=Path(__file__).with_name("v18-probe-load-guest.sh").read_bytes()
        script=v21_load_script(raw,4).decode()
        prefix=script[script.index("stats=/boot/"):script.index("for f in stream-a.mp4")]
        setup=script[script.index('(set -C; : > "$preflight")'):script.index("run=0")]
        with tempfile.TemporaryDirectory() as d:
            prefix=prefix.replace("/boot/home/config/settings",d)
            subprocess.run(["sh","-ec",prefix+setup+'(set -C; : > "$catchup"); c=1; x=100; y=200; cleanup'],check=True)
            self.assertEqual(list(Path(d).iterdir()),[])
            marker=Path(d)/"haiku-lab-video-deferred"
            marker.touch()
            r=subprocess.run(["sh","-ec",prefix+setup],capture_output=True)
            self.assertEqual(r.returncode,7)
            self.assertEqual(list(Path(d).iterdir()),[marker])
