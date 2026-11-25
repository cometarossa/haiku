"""Host tests of the actual FillBuffer method with a deterministic fake track."""
import re
import subprocess
import tempfile
import unittest
from pathlib import Path


class ProxyCatchupTest(unittest.TestCase):
    def test_bounded_progress_and_correct_output(self):
        root = Path(__file__).resolve().parents[3]
        source = (root / "src/apps/mediaplayer/supplier/ProxyVideoSupplier.cpp").read_text()
        method = re.search(r"status_t\nProxyVideoSupplier::FillBuffer\(.*?\n\}", source, re.S)
        self.assertIsNotNone(method)
        code = r'''
#include <cstdio>
#include <cstdlib>
#include <cassert>
using int64=long long;
using int32=int;
using uint32=unsigned int;
using uint64=unsigned long long;
using bigtime_t=long long;
using status_t=int;
#define B_PRId64 "lld"
const status_t B_OK=0, B_TIMED_OUT=-1, B_NO_INIT=-2, B_ERROR=-3;
bigtime_t clock_us=0;
bigtime_t system_time(){ return clock_us; }
struct media_raw_video_format { struct { uint32 line_width=320, line_count=180; } display; };
struct BAutolock { BAutolock(int&) {} };
struct Track {
    int64 current=0;
    int calls=0, seeks=0;
    int delay=100, step=1;
    bool fail=false, mismatch=false, seekFail=false;
    status_t readError=B_ERROR, seekError=B_ERROR;
    int64 CurrentFrame() { return current; }
    status_t SeekToFrame(int64* frame) {
        ++seeks;
        if (seekFail) return seekError;
        // Model the forward same-keyframe optimization, and backward seeks.
        if (*frame < current) current=0;
        *frame=current+(mismatch ? 1 : 0);
        return B_OK;
    }
    status_t ReadFrame(void* buf,bigtime_t*,const media_raw_video_format&,bool& cached) {
        ++calls;clock_us+=delay;
        if (fail) return readError;
        *static_cast<int64*>(buf)=current;
        current+=step;cached=false;
        return B_OK;
    }
};
struct Stats {
    bool enabled=true;
    int64 calls=0,cached=0,gap=0,seek=0,read=0,success=0,errors=0;
    void Gap(int64 frames){assert(frames>5);++gap;}
    status_t Finish(status_t ret,bool isSeek=false){
        if(ret==B_OK)++success;
        else if(ret==B_TIMED_OUT)++(isSeek?seek:read);
        else ++errors;
        return ret;
    }
};
struct ProxyVideoSupplier {
    Stats fLabProxyStats;
    int fSupplierLock=0;
    Track* fSupplier;
    bool fLabCatchup, fLabCatchupReported=false;
    bool fLabAdaptiveCatchup=false;
    bigtime_t fLabRecoveryAfter=0;
    bigtime_t fProcessingLatency=0;
    ProxyVideoSupplier(Track* t,bool on): fSupplier(t),fLabCatchup(on) {}
    status_t FillBuffer(int64,void*,const media_raw_video_format&,bool,bool&);
};
''' + method.group() + r'''
int main() {
    media_raw_video_format fmt;
    int64 output=-99;
    bool cached=false;
    Track t0; ProxyVideoSupplier off(&t0,false);
    assert(off.FillBuffer(10,&output,fmt,false,cached)==B_TIMED_OUT);
    assert(off.FillBuffer(11,&output,fmt,false,cached)==B_TIMED_OUT);
    assert(t0.current==0 && t0.calls==0 && output==-99);
    Track t1; ProxyVideoSupplier on(&t1,true);
    assert(on.FillBuffer(10,&output,fmt,false,cached)==B_TIMED_OUT);
    assert(t1.current==5 && t1.calls==5 && !cached);
    assert(on.FillBuffer(11,&output,fmt,false,cached)==B_TIMED_OUT);
    assert(t1.current==10 && t1.calls==10);
    assert(on.FillBuffer(12,&output,fmt,false,cached)==B_OK);
    assert(output==12 && t1.current==13 && !cached);
    assert(on.FillBuffer(12,&output,fmt,false,cached)==B_OK && cached);
    Track t2; t2.delay=2500; ProxyVideoSupplier slow(&t2,true);
    assert(slow.FillBuffer(10,&output,fmt,false,cached)==B_TIMED_OUT);
    assert(t2.calls==2 && t2.current==2); // soft budget, not a deadline
    Track t3; t3.step=0; ProxyVideoSupplier stuck(&t3,true);
    assert(stuck.FillBuffer(10,&output,fmt,false,cached)==B_TIMED_OUT);
    assert(t3.calls==1 && !stuck.fLabCatchupReported);
    Track t4; t4.fail=true; ProxyVideoSupplier failed(&t4,true);
    assert(failed.FillBuffer(10,&output,fmt,false,cached)==B_TIMED_OUT);
    assert(t4.calls==1 && !failed.fLabCatchupReported);
    Track t5; t5.mismatch=true; ProxyVideoSupplier mismatched(&t5,true);
    assert(mismatched.FillBuffer(10,&output,fmt,false,cached)==B_TIMED_OUT);
    assert(t5.calls==0);
    Track t6; ProxyVideoSupplier forced(&t6,true);
    assert(forced.FillBuffer(10,&output,fmt,true,cached)==B_OK);
    assert(output==10 && t6.calls==11 && !forced.fLabCatchupReported);
    Track t7; ProxyVideoSupplier normal(&t7,true);
    assert(normal.FillBuffer(4,&output,fmt,false,cached)==B_OK);
    assert(output==4 && t7.calls==5 && !normal.fLabCatchupReported);
    Track t8; t8.seekFail=true; ProxyVideoSupplier seekFailed(&t8,true);
    assert(seekFailed.FillBuffer(10,&output,fmt,false,cached)==B_ERROR);
    assert(t8.calls==0);
    Track t9; t9.current=20; ProxyVideoSupplier reverse(&t9,true);
    assert(reverse.FillBuffer(3,&output,fmt,false,cached)==B_OK);
    assert(output==3 && t9.calls==4 && !reverse.fLabCatchupReported);
    // Adaptive marker requires catch-up; HD never speculatively decodes.
    Track h; ProxyVideoSupplier hd(&h,true); hd.fLabAdaptiveCatchup=true;
    fmt.display.line_width=1280; fmt.display.line_count=720;
    assert(hd.FillBuffer(20,&output,fmt,false,cached)==B_TIMED_OUT);
    assert(h.calls==0 && h.current==0);
    assert(hd.FillBuffer(3,&output,fmt,true,cached)==B_OK && output==3);
    fmt.display.line_width=320; fmt.display.line_count=180;
    Track a; a.delay=5000; ProxyVideoSupplier adaptive(&a,true);
    adaptive.fLabAdaptiveCatchup=true;
    assert(adaptive.FillBuffer(20,&output,fmt,false,cached)==B_TIMED_OUT);
    assert(a.calls==1 && adaptive.fLabRecoveryAfter==clock_us+100000);
    assert(adaptive.FillBuffer(21,&output,fmt,false,cached)==B_TIMED_OUT);
    assert(a.calls==1);
    clock_us+=100000; a.delay=100;
    assert(adaptive.FillBuffer(22,&output,fmt,false,cached)==B_TIMED_OUT);
    assert(a.calls==6);
    Track e; e.fail=true; ProxyVideoSupplier errors(&e,true);
    errors.fLabAdaptiveCatchup=true;
    assert(errors.FillBuffer(20,&output,fmt,false,cached)==B_TIMED_OUT);
    assert(e.calls==1 && errors.fLabRecoveryAfter>clock_us);
    assert(errors.FillBuffer(21,&output,fmt,false,cached)==B_TIMED_OUT);
    assert(e.calls==1);
    Track disabled; ProxyVideoSupplier guardOnly(&disabled,false);
    guardOnly.fLabAdaptiveCatchup=true;
    assert(guardOnly.FillBuffer(20,&output,fmt,false,cached)==B_TIMED_OUT);
    assert(disabled.calls==0);
    assert(off.fLabProxyStats.calls==2 && off.fLabProxyStats.gap==2);
    assert(on.fLabProxyStats.calls==4 && on.fLabProxyStats.gap==2
        && on.fLabProxyStats.success==1 && on.fLabProxyStats.cached==1);
    Track seekTimeout; seekTimeout.seekFail=true; seekTimeout.seekError=B_TIMED_OUT;
    ProxyVideoSupplier st(&seekTimeout,false);
    assert(st.FillBuffer(10,&output,fmt,false,cached)==B_TIMED_OUT);
    assert(st.fLabProxyStats.seek==1 && st.fLabProxyStats.gap==0);
    Track readTimeout; readTimeout.fail=true; readTimeout.readError=B_TIMED_OUT;
    ProxyVideoSupplier rt(&readTimeout,false);
    assert(rt.FillBuffer(0,&output,fmt,false,cached)==B_TIMED_OUT);
    assert(rt.fLabProxyStats.read==1 && rt.fLabProxyStats.gap==0);
    return 0;
}
'''
        with tempfile.TemporaryDirectory() as folder:
            src=Path(folder)/"catchup.cpp"
            exe=Path(folder)/"catchup"
            src.write_text(code)
            subprocess.run(["c++","-std=c++11","-Wall","-Wextra","-Werror",str(src),"-o",str(exe)],check=True)
            subprocess.run([str(exe)],check=True)


if __name__ == "__main__":
    unittest.main()
