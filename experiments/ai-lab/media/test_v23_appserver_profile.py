import subprocess
import unittest
from pathlib import Path
from v18_probe_load_runner import v21_combined_script,observation_script,record_teardown_clocks
from v23_appserver_profile import profile_script,serial_profiles

class AppserverProfileTest(unittest.TestCase):
    def test_markers(self):
        raw=Path(__file__).with_name("v18-probe-load-guest.sh").read_bytes()
        src=observation_script(record_teardown_clocks(v21_combined_script(raw,4)),"on",4)
        for mode in ("off","on"):
            s=profile_script(src,mode)
            subprocess.run(["sh","-n"],input=s,check=True)
            self.assertEqual(s.count(b': > "$serverprofile"'),int(mode=="on"))
            self.assertEqual(s.count(b'"$observation" "$filltiming" "$serverprofile"'),2)
            self.assertIn(b'rm -f "$serverprofile"',s)
    def test_serial(self):
        self.assertEqual(serial_profiles("ordinary log","off",4),[])
        with self.assertRaises(ValueError):serial_profiles("ordinary log","on",4)
        lines=[]
        for team in range(1,5):
            for port in range(1,5):
                for phase in ("window","desktop_read","desktop_write","dispatch","sync","fill","bitmap","redraw","batch"):
                    n=3 if phase=="dispatch" else 1
                    lines.append(f"LAB_MEDIA_APPWIN team={team} port={port} phase={phase} n={n} us={n} max=1 ge50=0")
                lines.append(f"LAB_MEDIA_APPWIN_END team={team} port={port} normal=1")
        log="\n".join(lines)
        self.assertEqual(len(serial_profiles(log,"on",4)),16)
        with self.assertRaises(ValueError):serial_profiles(log,"off",4)
        with self.assertRaises(ValueError):serial_profiles(log,"on",8)

    def test_associate_trials(self):
        import tempfile
        from v23_appserver_profile import associate_trials
        with tempfile.TemporaryDirectory() as d:
            root=Path(d)
            rows=[{"tag":str(i)} for i in range(4)]
            for i in range(4):
                (root/f"{i}.team").write_text(str(100+i)+"\n")
            windows=[dict(team=100+i,bitmap={"n":1}) for i in range(4) for _ in range(4)]
            result=associate_trials(root,rows,list(reversed(windows)),"on",4)
            self.assertEqual(result["0"][0]["team"],100)
            self.assertEqual(len(result["3"]),4)
            with self.assertRaises(ValueError):associate_trials(root,rows,windows[:-1],"on",4)
            with self.assertRaises(ValueError):associate_trials(root,rows,windows+[dict(team=999,bitmap={"n":1})],"on",4)
            self.assertEqual(associate_trials(root,rows,[],"off",4),{str(i):[] for i in range(4)})
            (root/"3.team").write_text("100\n")
            with self.assertRaises(ValueError):associate_trials(root,rows,windows,"on",4)
