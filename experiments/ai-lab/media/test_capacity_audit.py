import unittest
import tempfile
from pathlib import Path
from capacity_audit import audit_trial
from test_media_stats_report import P,C


class CapacityAuditTest(unittest.TestCase):
    def test_invalid_duration_retains_independent_latency(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);tag="00-n4-off";n=4
            def write(ext,s):
                (root/(tag+"."+ext)).write_text(s)
            for ext,value in dict(start=1000000,dispatch=4000000,play=5000000,
                                  stop=21000000,**{"quit-time":22000000},exit=0).items():
                write(ext,str(value))
            write("windows","".join(f"{k} {k*2}\n" for k in range(1,n+1)))
            write("positions","".join(f"SAMPLE {s}\n"+"".join(
                f"WINDOW {k*2}\n{tag}-{k}.mp4\ntrue\nReply BMessage(B_REPLY):\n"
                f'   "result" (B_INT64_TYPE) : {s*2000000+k} (0x0)\n'
                for k in range(1,n+1)) for s in (1,2,3)))
            write("stdout","LAB_MEDIA_OVERLAY_PREFLIGHT software format=8\n"*n)
            write("stderr","".join(P.replace("thread=123",f"thread={k+100}")+"\n"+C+"\n" for k in range(n)))
            clock=5000000
            rows=[]
            for s in (1,2,3):
                for k in range(1,n+1):
                    for op,dt in (("title",1000),("playing",2000),("position",3000)):
                        rows.append(f"{s} {k*2} {op} {clock} {clock+dt} 0")
                        clock+=dt+100
            write("latency","\n".join(rows)+"\n")
            r=audit_trial(root,0,n,"off")
            self.assertFalse(r["valid"])
            self.assertIn("duration",r["acceptance_error"])
            self.assertEqual(r["playing_replies"],12)
            self.assertEqual(r["latency_by_operation"]["position"]["p95_us"],3000)
            self.assertEqual(r["play_dispatch_us"],1000000)
            self.assertEqual(r["query_latency"]["count"],36)
            # Timing integrity is never relaxed for a failed trial.
            write("latency","\n".join(rows[:-1])+"\n")
            with self.assertRaises(ValueError):
                audit_trial(root,0,n,"off")
