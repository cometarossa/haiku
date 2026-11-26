import unittest
import tempfile
import subprocess
import re
from pathlib import Path
from fill_timing_report import validate
from test_media_stats_report import P

R="LAB_MEDIA_FILL_TIMING thread=123 ok=90 cached=6 timeout=2 end=1 error=1 ok_us=450000 cached_us=20000 timeout_us=20000 end_us=5000 error_us=5000"


class FillTimingTest(unittest.TestCase):
    def test_conservation(self):
        self.assertEqual(validate(P+"\n"+R)[0]["timeout_us"],20000)
        for bad in (R.replace("ok=90","ok=89"),R.replace("error_us=5000","error_us=5001"),R.replace("thread=123","thread=124"),R+"\n"+R):
            with self.assertRaises(ValueError):validate(P+"\n"+bad)
        self.assertEqual(validate(P,False),[])
        with self.assertRaises(ValueError):validate(P+"\n"+R,False)
    def test_actual_outcome_method(self):
        root=Path(__file__).resolve().parents[3]
        source=(root/"src/apps/mediaplayer/media_node_framework/video/VideoProducer.cpp").read_text()
        method=re.search(r"    void RecordFillOutcome\(.*?\n    \}",source,re.S).group()
        code=r"""
#include <cassert>
using status_t=int;
using bigtime_t=long long;
const status_t B_OK=0,B_TIMED_OUT=-1,B_LAST_BUFFER_ERROR=-2;
struct Stats {
 bool timingEnabled=true;
 unsigned long long fillOutcomeCount[5]={};
 bigtime_t fillOutcomeUs[5]={};
"""+method+r"""
};
int main(){
 Stats s;
 s.RecordFillOutcome(B_OK,false,10);
 s.RecordFillOutcome(B_OK,true,20);
 s.RecordFillOutcome(B_TIMED_OUT,true,30);
 s.RecordFillOutcome(B_LAST_BUFFER_ERROR,false,40);
 s.RecordFillOutcome(-3,false,50);
 for(int i=0;i<5;i++){assert(s.fillOutcomeCount[i]==1);assert(s.fillOutcomeUs[i]==(i+1)*10);}
 s.timingEnabled=false;
 s.RecordFillOutcome(B_OK,false,100);
 assert(s.fillOutcomeCount[0]==1 && s.fillOutcomeUs[0]==10);
}
"""
        with tempfile.TemporaryDirectory() as d:
            src=Path(d)/"test.cpp";exe=Path(d)/"test"
            src.write_text(code)
            subprocess.run(["c++","-std=c++11","-Wall","-Wextra","-Werror",str(src),"-o",str(exe)],check=True)
            subprocess.run([str(exe)],check=True)
