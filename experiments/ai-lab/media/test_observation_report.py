import unittest
import subprocess
import tempfile
from pathlib import Path
from observation_report import parse

class ObservationTest(unittest.TestCase):
    def test_native_bins(self):
        root=Path(__file__).resolve().parents[3]/"src/apps/mediaplayer"
        os=r"""
#pragma once
using int64=long long;using bigtime_t=long long;
#define B_PRId64 "lld"
extern long long now;extern int reads;
inline bigtime_t system_time(){++reads;return now;}
inline int64 atomic_get64(int64* p){return __atomic_load_n(p,__ATOMIC_ACQUIRE);}
inline int64 atomic_add64(int64* p,int64 v){return __atomic_fetch_add(p,v,__ATOMIC_SEQ_CST);}
"""
        src=r"""
#include <cassert>
#include <unistd.h>
bool marker=true;
int fake_access(const char*,int){return marker?0:-1;}
#define access fake_access
#include "LabObservationStats.h"
#undef access
long long now=1234567;int reads=0;
int main(){
 LabObservationStats off(false);off.Record(0);off.Report("view",1);
 assert(reads==0);
 LabObservationStats on(true);
 on.Record(2,1234567);on.Record(2,1999999);
 on.Record(5,2000000);now=3000000;on.Report("producer",2);
 LabObservationStats overflow(true);overflow.Record(0,now+512000000);
 overflow.Report("view",3);
}
"""
        with tempfile.TemporaryDirectory() as d:
            p=Path(d);(p/"OS.h").write_text(os);(p/"test.cpp").write_text(src)
            subprocess.run(["c++","-std=c++11","-Wall","-Wextra","-Werror","-I",d,"-I",str(root),str(p/"test.cpp"),"-o",str(p/"test")],check=True)
            log=subprocess.run([str(p/"test")],capture_output=True,text=True,check=True).stderr
        good,bad=log.split("LAB_OBSERVATION stage=view id=3")
        r=parse(good)[("producer",2)]
        self.assertEqual(r["bins"][1000000][2],2)
        self.assertEqual(r["bins"][2000000][5],1)
        with self.assertRaises(ValueError):parse("LAB_OBSERVATION stage=view id=3"+bad)
        with self.assertRaises(ValueError):parse(good+good)

    def test_window_and_conservation(self):
        from observation_report import summarize
        from test_media_stats_report import P
        view="LAB_VIDEO_VIEW calls=10 null=1 looper_fail=1 bitmap_fail=0 overlay=0 invalidate=0 draw=8 total_us=10 update_us=0 looper_us=0 bitmap_us=0 overlay_us=0 invalidate_us=0 draw_us=0"
        def record(stage,ident,rows):
            h=f"LAB_OBSERVATION stage={stage} id={ident} anchor=1000000 created=1100000 ended=5100000 overflow=0 valid=1"
            return h+"\n"+"\n".join(f"LAB_OBSERVATION_BIN stage={stage} id={ident} bin={t} "+" ".join(f"c{i}={v}" for i,v in enumerate(c)) for t,c in rows)
        producer=record("producer",123,[(1000000,[20,0,0,0,0,20,0,0]),(2000000,[30,0,1,0,0,30,1,0]),(3000000,[40,6,1,1,1,44,4,1])])
        visual=record("view",456,[(1000000,[1,0,0,0,0,2,0,0]),(2000000,[0,1,0,0,0,4,0,0]),(3000000,[0,0,0,0,0,2,0,0])])
        log="\n".join((P,view,producer,visual))
        r=summarize(log,1500000,3900000,1)
        self.assertEqual(r["seconds"],1)
        self.assertEqual(r["draw_completions"],4)
        self.assertEqual(r["stages"]["producer"]["observed"]["timeout"],1)
        with self.assertRaises(ValueError):summarize(log.replace("c5=4 c6=0","c5=5 c6=0"),1500000,3900000,1)
        with self.assertRaises(ValueError):summarize(log,500000,3900000,1)
