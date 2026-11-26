import subprocess
import unittest
from pathlib import Path
from v18_probe_load_runner import record_teardown_clocks,v22_gop_script,v21_combined_script,v21_load_script

class TeardownTest(unittest.TestCase):
    def test_all_load_variants(self):
        raw=Path(__file__).with_name("v18-probe-load-guest.sh").read_bytes()
        for f in (v21_load_script,v21_combined_script,v22_gop_script):
            for n in (4,8,16):
                s=record_teardown_clocks(f(raw,n)).decode()
                subprocess.run(["sh","-n"],input=s,text=True,check=True)
                self.assertEqual(s.count('curl -fsS -T "$tag.quit-time"'),1)
                self.assertLess(s.index('system_time > "$tag.quit-time"'),s.index('system_time > "$tag.quit-return"'))
                self.assertLess(s.index('system_time > "$tag.quit-return"'),s.index('system_time > "$tag.exit-time"'))
                self.assertIn('for ext in start quit-return exit-time windows',s)
