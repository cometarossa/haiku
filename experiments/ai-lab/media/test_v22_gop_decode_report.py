import tempfile
import unittest
from pathlib import Path
from v22_gop_decode_report import validate,HASHES,TAGS,ORDER
from test_v21_decode_report import log

def frames_for(g):
    return "".join(f"FRAME {i} {round(i*1000000/30)} {g*3600+i:016x}\n" for i in range(3600))+"frames,width,height,format,hash_fnv1a64\n3600,320,180,B_RGB32,0123456789abcdef\n"

class GopDecodeTest(unittest.TestCase):
    def test_gate(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)
            (p/"done.txt").write_text("0")
            (p/"revision.txt").write_text("ai_2f9d27bf")
            (p/"input-sha256.txt").write_text("".join(f"{h}  gop-{g}.mp4\n" for g,h in HASHES.items()))
            for i,(tag,g) in enumerate(zip(TAGS,ORDER)):
                for ext,value in (("stdout",frames_for(g)),("stderr",log(1)),("exit","0"),("start",str(i*20+1)),("stop",str(i*20+10))):
                    (p/(tag+"."+ext)).write_text(value)
            self.assertTrue(validate(p)["valid"])
            (p/(TAGS[2]+".stdout")).write_text(frames_for(120))
            with self.assertRaisesRegex(ValueError,"same-file"):validate(p)
