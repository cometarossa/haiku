import tempfile
import unittest
from pathlib import Path
from v16_catchup_report import validate, validate_run, SPECS
from test_media_stats_report import P, C


class CatchupReportTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.write("revision.txt", "hrev60465+ai_a1b69d83\n")
        self.write("done.txt", "0\n")
        for index,(n,state) in enumerate(SPECS):
            tag=f"{index:02d}-n{n}-{state}"
            for ext,value in dict(start=1000000,play=5000000,stop=13000000,**{"quit-time":14000000},exit=0).items():
                self.write(f"{tag}.{ext}",f"{value}\n")
            self.write(tag+".windows","".join(f"{k} {k*2}\n" for k in range(1,n+1)))
            self.write(tag+".positions","".join(
                f"SAMPLE {i}\n"+"".join(
                    f"WINDOW {k*2}\n{tag}-{k}.mp4\ntrue\nReply BMessage(B_REPLY):\n"
                    f'   "result" (B_INT64_TYPE) : {i*2000000+k} (0x0)\n'
                    for k in range(1,n+1))
                for i in range(1,4)))
            self.write(tag+".stdout","LAB_MEDIA_OVERLAY_PREFLIGHT software format=8\n"*n)
            self.write(tag+".stderr","".join(P.replace("thread=123",f"thread={k+100}")+"\n"+C+"\n" for k in range(n))+
                       ("LAB_MEDIA_CATCHUP progress from=5 to=6\n" if state=="on" else ""))
    def write(self,name,value):
        (self.root/name).write_text(value)
    def edit(self,name,old,new):
        p=self.root/name
        p.write_text(p.read_text().replace(old,new))
    def test_complete_balanced(self):
        r=validate(self.root)
        self.assertEqual(r["completed"],8)
        self.assertEqual(r["activated_pairs"],4)
        self.assertEqual(len(r["pairs"]),4)
        self.assertEqual([p["n"] for p in r["pairs"]],[4,4,8,8])
    def test_partial(self):
        (self.root/"02-n4-on.exit").unlink()
        r=validate(self.root,partial=True)
        self.assertEqual(r["completed"],2)
        self.assertEqual(len(r["pairs"]),1)
    def test_no_activation_not_proof(self):
        self.edit("01-n4-on.stderr","LAB_MEDIA_CATCHUP progress from=5 to=6\n","")
        self.assertEqual(validate(self.root)["activated_pairs"],3)
    def test_marker_leak(self):
        p=self.root/"00-n4-off.stderr"
        p.write_text(p.read_text()+"LAB_MEDIA_CATCHUP progress from=5 to=6\n")
        with self.assertRaises(ValueError):validate(self.root)
    def test_invalid_progress(self):
        self.edit("01-n4-on.stderr","from=5 to=6","from=5 to=5")
        with self.assertRaises(ValueError):validate(self.root)
    def test_window_mismatch(self):
        self.edit("00-n4-off.windows","2 4","2 2")
        with self.assertRaises(ValueError):validate(self.root)
    def test_not_advancing(self):
        self.edit("00-n4-off.positions","6000001","4000001")
        with self.assertRaises(ValueError):validate(self.root)
    def test_wrong_duration(self):
        self.write("00-n4-off.stop","10000000\n")
        with self.assertRaises(ValueError):validate(self.root)
    def test_wrong_revision(self):
        self.write("revision.txt","ai_db20e3f2")
        with self.assertRaises(ValueError):validate(self.root)
    def test_overlay_failure(self):
        self.write("00-n4-off.stdout","trying without overlays\n")
        with self.assertRaises(ValueError):validate(self.root)
    def test_bad_record(self):
        self.edit("00-n4-off.stderr","attempts=101","attempts=103")
        with self.assertRaises(ValueError):validate(self.root)
    def test_incomplete(self):
        self.write("done.txt","1\n")
        with self.assertRaises(ValueError):validate(self.root)
