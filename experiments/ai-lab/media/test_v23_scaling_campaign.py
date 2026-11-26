import subprocess
import unittest
from pathlib import Path
from v18_probe_load_runner import v21_combined_script,record_teardown_clocks,observation_script
from v23_scaling_campaign import scaling_script

class ScalingScriptTest(unittest.TestCase):
    def test_generated(self):
        raw=Path(__file__).with_name("v18-probe-load-guest.sh").read_bytes()
        src=observation_script(record_teardown_clocks(v21_combined_script(raw,4)),"on",4)
        s=scaling_script(src,"a"*64)
        subprocess.run(["sh","-n"],input=s,check=True)
        self.assertIn(b'v23-scaling-backup-4',s)
        self.assertNotIn(b': > "$catchup"',s)
        self.assertEqual(s.count(b'mv "$backup/original" "$settings"'),1)
        self.assertIn(b'curl -fsS -T settings-restored.txt',s)
        self.assertLess(s.index(b'mv "$settings" "$backup/original"'),s.index(b'own_scaling=1'))
        with self.assertRaises(ValueError):scaling_script(src,"bad")

    def test_restoration_and_running_guard(self):
        import hashlib
        import tempfile
        raw=Path(__file__).with_name("v18-probe-load-guest.sh").read_bytes()
        src=observation_script(record_teardown_clocks(v21_combined_script(raw,4)),"on",4)
        original=b"original settings"
        s=scaling_script(src,hashlib.sha256(original).hexdigest()).decode()
        block=s[s.index("cleanup() {"):s.index(' if test "$own_observation" = 1;')]
        with tempfile.TemporaryDirectory() as d:
            root=Path(d); backup=root/"backup";backup.mkdir()
            settings=root/"settings";settings.write_bytes(b"temporary")
            (backup/"original").write_bytes(original)
            prefix='set -e\nsettings="$1"; backup="$2"; expected_settings="$3"; own_scaling=1; pid=; app=x\nhey() { return 1; }\nsha256sum() { shasum -a 256 "$@"; }\n'
            args=[str(settings),str(backup),hashlib.sha256(original).hexdigest()]
            proc=subprocess.run(["sh","-c",prefix+block+'}\npid=$$; cleanup',"sh",*args],capture_output=True)
            self.assertNotEqual(proc.returncode,0)
            self.assertEqual(settings.read_bytes(),b"temporary")
            self.assertEqual((backup/"original").read_bytes(),original)
            subprocess.run(["sh","-c",prefix+block+'}\ncleanup',"sh",*args],check=True)
            self.assertEqual(settings.read_bytes(),original)
            self.assertEqual((backup/"final-generated").read_bytes(),b"temporary")
            self.assertFalse((backup/"original").exists())

    def test_capacity_variants(self):
        raw=Path(__file__).with_name("v18-probe-load-guest.sh").read_bytes()
        for n in (8,16):
            src=observation_script(record_teardown_clocks(v21_combined_script(raw,n)),"on",n)
            s=scaling_script(src,"a"*64,n)
            subprocess.run(["sh","-n"],input=s,check=True)
            self.assertIn(f"v23-scaling-backup-{n}".encode(),s)
            self.assertIn(f"v23-scaling-{n}-ram".encode(),s)
            self.assertNotIn(b': > "$catchup"',s)
