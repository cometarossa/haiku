"""Compile the real deferred-notification helper against controlled primitives."""
import subprocess
import tempfile
import unittest
from pathlib import Path


class NativeDeferredHelperTest(unittest.TestCase):
    def test_reservation_and_sticky_disable(self):
        root=Path(__file__).resolve().parents[3]
        headers={
            "OS.h":r'''
#pragma once
using int32=int;
using uint32=unsigned;
using int64=long long;
using bigtime_t=long long;
extern bigtime_t fake_clock;
inline bigtime_t system_time(){return fake_clock;}
#define B_PRId64 "lld"
inline int32 atomic_get(int32* p){return __atomic_load_n(p,__ATOMIC_SEQ_CST);}
inline int32 atomic_test_and_set(int32* p,int32 v,int32 expected){
    __atomic_compare_exchange_n(p,&expected,v,false,__ATOMIC_SEQ_CST,__ATOMIC_SEQ_CST);
    return expected;
}
inline void atomic_set(int32* p,int32 v){__atomic_store_n(p,v,__ATOMIC_SEQ_CST);}
inline void atomic_set64(int64* p,int64 v){__atomic_store_n(p,v,__ATOMIC_SEQ_CST);}
inline int64 atomic_add64(int64* p,int64 v){return __atomic_fetch_add(p,v,__ATOMIC_SEQ_CST);}
inline int64 atomic_get64(int64* p){return __atomic_load_n(p,__ATOMIC_SEQ_CST);}
constexpr int B_OK=0;
''',
            "Message.h":r'''
#pragma once
#include "OS.h"
struct BMessage { explicit BMessage(uint32 code):what(code){} uint32 what; };
''',
            "Messenger.h":r'''
#pragma once
#include "Message.h"
#include <cassert>
struct BHandler {};
extern bool failAttach,failSend;
extern int sends,attaches;
extern void (*onSend)();
struct BMessenger {
    int SetTo(BHandler* h){assert(h);++attaches;return failAttach?-1:0;}
    int SendMessage(BMessage* m,BMessenger,int timeout){
        assert(m->what==123 && timeout==0);++sends;
        if(failSend)return -1;
        if(onSend)onSend();
        return 0;
    }
};
'''
        }
        source=r'''
#include <cassert>
#include <cstring>
#include <unistd.h>
bool marker=false,timing=false,failAttach=false,failSend=false;
long long fake_clock=0;
int sends=0,attaches=0;
void (*onSend)()=nullptr;
int fake_access(const char* p,int mode){
    assert(mode==F_OK);
    if(strcmp(p,"/boot/home/config/settings/haiku-lab-video-deferred-timing")==0)
        return timing?0:-1;
    if(strcmp(p,"/boot/home/config/settings/haiku-lab-video-observation")==0) return -1;
    assert(strcmp(p,"/boot/home/config/settings/haiku-lab-video-deferred")==0);
    return marker?0:-1;
}
#define access fake_access
#include "LabDeferredVideo.h"
#undef access
LabDeferredVideo* active=nullptr;
void inline_handler(){assert(active->BeginHandle());active->FinishHandle(true);}
int main(){
    BHandler target;
    LabDeferredVideo off;
    off.Attach(&target);assert(!off.TryQueue(123));assert(!off.Enabled());
    off.Report();assert(!sends&&!attaches);
    marker=true;
    LabDeferredVideo v;
    assert(!v.TryQueue(123));v.Attach(&target);assert(v.Enabled());
    v.Attach(&target);assert(attaches==1);
    assert(v.TryQueue(123));for(int i=0;i<100;i++)assert(v.TryQueue(123));
    assert(sends==1);assert(v.BeginHandle());v.FinishHandle(true);
    failSend=true;assert(!v.TryQueue(123));assert(v.Enabled());
    failSend=false;assert(v.TryQueue(123));assert(v.BeginHandle());v.FinishHandle(false);
    active=&v;onSend=inline_handler;assert(v.TryQueue(123));onSend=nullptr;
    assert(v.TryQueue(123));v.Disable();assert(!v.BeginHandle());
    assert(!v.Enabled()&&!v.TryQueue(123));v.Attach(&target);assert(!v.Enabled());
    v.Report();
    LabDeferredVideo blocked;blocked.Disable();blocked.Attach(&target);
    assert(!blocked.Enabled());
    failAttach=true;LabDeferredVideo invalid;invalid.Attach(&target);
    assert(!invalid.Enabled()&&!invalid.TryQueue(123));
    timing=true;failAttach=false;
    LabDeferredVideo timed;timed.Attach(&target);
    fake_clock=100;assert(timed.TryQueue(123));
    fake_clock=170;assert(timed.TryQueue(123));assert(timed.BeginHandle());
    timed.FinishHandle(true,40,10,20);
    fake_clock=250;assert(timed.TryQueue(123));
    fake_clock=300;assert(timed.BeginHandle());
    timed.FinishHandle(false,12,9,0);
    timed.Report();
    return 0;
}
'''
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)
            for name,body in headers.items():(p/name).write_text(body)
            (p/"test.cpp").write_text(source)
            subprocess.run(["c++","-std=c++11","-Wall","-Wextra","-Werror","-I",d,"-I",str(root/"src/apps/mediaplayer"),str(p/"test.cpp"),"-o",str(p/"test")],check=True)
            r=subprocess.run([str(p/"test")],check=True,capture_output=True,text=True)
        lines=[l for l in r.stderr.splitlines() if l.startswith("LAB_VIDEO_DEFERRED ")]
        self.assertEqual(len(lines),2)
        self.assertEqual(dict((k,int(v)) for k,v in (s.split("=") for s in lines[0].split()[1:])),
            dict(queued=4,coalesced=100,failed=1,handled=3,cancelled=1,draw=2,skipped=1))

        timing_lines=[l for l in r.stderr.splitlines() if l.startswith("LAB_VIDEO_DEFERRED_TIMING ")]
        self.assertEqual(timing_lines,["LAB_VIDEO_DEFERRED_TIMING queue_us=120 handler_us=52 bitmap_us=19 draw_us=20"])
