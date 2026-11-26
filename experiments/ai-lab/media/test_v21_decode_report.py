import tempfile
import unittest
from pathlib import Path
from v21_decode_report import frames,threads,validate,FIXTURE_SHA,REV

def fixture():
    return "".join(f"FRAME {i} {round(i*1000000/30)} {i:016x}\n" for i in range(600))+"frames,width,height,format,hash_fnv1a64\n600,320,180,B_RGB32,0123456789abcdef\n"

def log(n):
    return f"LAB_VIDEO_THREADS codec=h264 width=320 height=180 original=4 requested={n} effective={n} active_type=0\n"

class V21DecodeTest(unittest.TestCase):
    def test_repeat_upload_names(self):
        from v21_decode_runner import repeat_script
        import subprocess
        script=repeat_script(Path(__file__).with_name("v21-decode-smoke-guest.sh").read_bytes())
        subprocess.run(["sh","-n"],input=script,check=True)
        self.assertIn(b'curl -fsS -T "$tag.$ext" "$base/$tag.$ext"',script)
        self.assertNotIn(b'$base/$state.',script)
        self.assertIn(b'for state in off on on off off on on off;',script)
    def test_frames(self):
        self.assertEqual(len(frames(fixture())[0]),600)
        for bad in (fixture().replace("FRAME 1 ","FRAME 2 ",1),
                    fixture().replace("33333 ","93333 ",1),
                    fixture().replace("600,320,180","600,640,480")):
            with self.assertRaises(ValueError):frames(bad)
    def test_threads(self):
        self.assertEqual(threads(log(1),"on")[0]["effective"],1)
        self.assertEqual(threads(log(4),"off")[0]["requested"],4)
        for bad in (log(4),log(1).replace("effective=1","effective=4"),""):
            with self.assertRaises(ValueError):threads(bad,"on")
    def test_pair(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)
            for name,value in (("done.txt","0\n"),("revision.txt","ai_"+REV),
                               ("input-sha256.txt",FIXTURE_SHA+"  stream-a.mp4\n")):
                (p/name).write_text(value)
            for state,n in (("off",4),("on",1)):
                for ext,value in (("stdout",fixture()),("stderr",log(n)),("exit","0"),("start","10"),("stop","20")):
                    (p/(state+"."+ext)).write_text(value)
            self.assertTrue(validate(p)["identical"])
            (p/"on.stdout").write_text(fixture().replace("FRAME 1 33333 0000000000000001","FRAME 1 33333 000000000000ffff"))
            with self.assertRaisesRegex(ValueError,"pixel or timestamp"):validate(p)
