import tempfile
import unittest
from pathlib import Path
from v16_catchup_report import validate, validate_run, SPECS, SPECS_16
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
    def test_sixteen_stream_campaign(self):
        for index,(n,state) in enumerate(SPECS_16):
            tag=f"{index:02d}-n{n}-{state}"
            for ext,value in dict(start=1000000,play=5000000,stop=17000000,**{"quit-time":18000000},exit=0).items():
                self.write(f"{tag}.{ext}",f"{value}\n")
            self.write(tag+".windows","".join(f"{k} {k*2}\n" for k in range(1,n+1)))
            self.write(tag+".positions","".join(
                f"SAMPLE {i}\n"+"".join(
                    f"WINDOW {k*2}\n{tag}-{k}.mp4\ntrue\nReply BMessage(B_REPLY):\n"
                    f'   "result" (B_INT64_TYPE) : {i*3000000+k} (0x0)\n'
                    for k in range(1,n+1)) for i in range(1,4)))
            self.write(tag+".stdout","LAB_MEDIA_OVERLAY_PREFLIGHT software format=8\n"*n)
            self.write(tag+".stderr","".join(P.replace("thread=123",f"thread={k+100}")+"\n"+C+"\n" for k in range(n))+
                       ("LAB_MEDIA_CATCHUP progress from=5 to=6\n" if state=="on" else ""))
        r=validate(self.root,specs=SPECS_16)
        self.assertEqual(r["completed"],4)
        self.assertEqual(r["activated_pairs"],2)
        self.assertEqual([p["n"] for p in r["pairs"]],[16,16])
        self.write("00-n16-off.stop","16000000\n")
        with self.assertRaises(ValueError):validate(self.root,specs=SPECS_16)

    def test_adaptive_hd_guard(self):
        self.write("revision.txt","ai_f960376e")
        with self.assertRaises(ValueError):
            validate(self.root,revision="f960376e",require_no_activation=True)
        for i,(n,state) in enumerate(SPECS):
            if state=="on":
                self.edit(f"{i:02d}-n{n}-{state}.stderr","LAB_MEDIA_CATCHUP progress from=5 to=6\n","")
        self.assertEqual(validate(self.root,revision="f960376e",require_no_activation=True)["activated_pairs"],0)

    def test_query_latency(self):
        tag="00-n4-off"
        rows=[]
        clock=5000000
        for sample in (1,2,3):
            for win in (2,4,6,8):
                for op in ("title","playing","position"):
                    rows.append(f"{sample} {win} {op} {clock} {clock+1000} 0")
                    clock+=2000
        self.write(tag+".latency","\n".join(rows)+"\n")
        r=validate_run(self.root,0,4,"off",True)
        self.assertEqual(r["query_latency"],dict(count=36,median_us=1000,p95_us=1000,max_us=1000,total_us=36000))
        self.write(tag+".latency","\n".join(rows[:-1])+"\n")
        with self.assertRaises(ValueError):validate_run(self.root,0,4,"off",True)
        self.write(tag+".latency","\n".join(rows).replace("5000000 5001000 0","5000000 5001000 1")+"\n")
        with self.assertRaises(ValueError):validate_run(self.root,0,4,"off",True)

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
