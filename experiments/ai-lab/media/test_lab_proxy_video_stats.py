"""Compile actual proxy counters against minimal host-compatible Haiku types."""
import subprocess
import tempfile
import unittest
from pathlib import Path
from proxy_video_stats_report import parse

class LabProxyStatsTest(unittest.TestCase):
    def test_real_helper_reset_and_classification(self):
        root=Path(__file__).resolve().parents[3]
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)
            (p/"OS.h").write_text(r'''
#pragma once
using int64=long long;
using status_t=int;
#define B_PRId64 "lld"
constexpr status_t B_OK=0,B_TIMED_OUT=-1,B_ERROR=-2;
''')
            (p/"test.cpp").write_text(r'''
#include <cassert>
#include <cstring>
#include <unistd.h>
bool marker=false;
int fake_access(const char* path,int mode) {
    assert(strcmp(path,"/boot/home/config/settings/haiku-lab-video-proxy-stats")==0);
    assert(mode==F_OK);
    return marker?0:-1;
}
#define access fake_access
#include "LabProxyVideoStats.h"
#undef access
int main(){
    LabProxyVideoStats off;
    assert(!off.enabled);
    assert(off.Finish(B_TIMED_OUT)==B_TIMED_OUT);
    off.Gap(10);off.ReportAndReset();assert(off.gapTimeout==0);
    marker=true;LabProxyVideoStats s;
    assert(s.enabled);
    s.calls=6;s.cached=1;
    s.Gap(9);s.Gap(15);
    assert(s.Finish(B_TIMED_OUT,true)==B_TIMED_OUT);
    assert(s.Finish(B_TIMED_OUT)==B_TIMED_OUT);
    assert(s.Finish(B_OK)==B_OK);
    s.ReportAndReset();
    assert(s.calls==0 && s.maxGap==0 && s.gapFrames==0);
    ++s.calls;assert(s.Finish(B_ERROR)==B_ERROR);
    s.ReportAndReset();
    return 0;
}
''')
            subprocess.run(["c++","-std=c++11","-Wall","-Wextra","-Werror","-I",d,"-I",str(root/"src/apps/mediaplayer/supplier"),str(p/"test.cpp"),"-o",str(p/"test")],check=True)
            r=subprocess.run([str(p/"test")],check=True,capture_output=True,text=True)
        a,b=parse(r.stderr)
        self.assertEqual(a,dict(calls=6,cached=1,gap_timeout=2,seek_timeout=1,read_timeout=1,other_errors=0,success=1,gap_frames=24,max_gap=15))
        self.assertEqual(b,dict(calls=1,cached=0,gap_timeout=0,seek_timeout=0,read_timeout=0,other_errors=1,success=0,gap_frames=0,max_gap=0))
