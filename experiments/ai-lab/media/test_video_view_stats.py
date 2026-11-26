"""Compile the actual SetBitmap body with fake view/target/clock primitives."""
import re
import subprocess
import tempfile
import unittest
from pathlib import Path


class VideoViewStatsTest(unittest.TestCase):
    def test_actual_set_bitmap_paths(self):
        root = Path(__file__).resolve().parents[3]
        app = root / "src/apps/mediaplayer"
        method = re.search(r"void\nVideoView::SetBitmap\(.*?\n\}", (app/"VideoView.cpp").read_text(), re.S)
        self.assertIsNotNone(method)
        os_header = r'''
#pragma once
using int64=long long;
using bigtime_t=long long;
#define B_PRId64 "lld"
extern bigtime_t clock_us;
extern int reads;
inline bigtime_t system_time() { ++reads; return clock_us; }
inline int64 atomic_add64(int64* p,int64 v) { return __atomic_fetch_add(p,v,__ATOMIC_SEQ_CST); }
inline int64 atomic_get64(int64* p) { return __atomic_load_n(p,__ATOMIC_ACQUIRE); }
'''
        source = r'''
#include <cassert>
#include <unistd.h>
#include <cstring>
bool marker=false;
int lab_access(const char* path,int mode) {
    if(strcmp(path,"/boot/home/config/settings/haiku-lab-video-observation")==0) return -1;
    assert(strcmp(path,"/boot/home/config/settings/haiku-lab-video-view-stats")==0);
    assert(mode==F_OK);
    return marker ? 0 : -1;
}
#define access lab_access
#include "VideoViewStats.h"
#undef access
bigtime_t clock_us=0;
int reads=0;
using status_t=int;
const int B_OK=0, B_BITMAP_WILL_OVERLAY=1, B_FOLLOW_ALL=2;
const int B_OVERLAY_FILTER_HORIZONTAL=4,B_OVERLAY_FILTER_VERTICAL=8;
const int B_OVERLAY_TRANSFER_CHANNEL=16,B_SOLID_LOW=0,B_TRANSPARENT_COLOR=0;
struct BRect {
    BRect operator|(BRect) const { return {}; }
    bool Intersects(BRect) const { return true; }
};
struct rgb_color {};
struct overlay_restrictions {};
struct BBitmap {
    int flags=0;
    int Flags() const { return flags; }
    BRect Bounds() const { return {}; }
    status_t GetOverlayRestrictions(overlay_restrictions*) const { return B_OK; }
};
void snooze(int us) { clock_us+=us; }
struct VideoTarget {
    void SetBitmap(const BBitmap*) { clock_us+=3; }
};
const int MSG_LAB_DEFERRED_VIDEO=1;
struct DeferredStub { bool Enabled(){return false;} void Disable(){} bool TryQueue(int){return false;} };
struct VideoView : VideoTarget {
    DeferredStub fLabDeferred;
    LabVideoViewStats fLabViewStats;
    bool fOverlayMode=false, fSubtitleChanged=false,fHasSubtitle=false;
    bool looper_ok=true,bitmap_ok=true, overlay_ok=true;
    int draws=0, invalidations=0, looperLocks=0, bitmapLocks=0;
    BRect fVideoFrame,fSubtitleFrame;
    rgb_color fOverlayKeyColor;
    overlay_restrictions fOverlayRestrictions;
    status_t LockLooperWithTimeout(int us) {
        assert(us==10000); clock_us+=5;
        if(looper_ok) ++looperLocks;
        return looper_ok ? B_OK : -1;
    }
    bool LockBitmap(){ clock_us+=7; if(bitmap_ok) ++bitmapLocks; return bitmap_ok; }
    void UnlockBitmap(){ assert(bitmapLocks==1); --bitmapLocks; clock_us+=1; }
    void UnlockLooper(){ assert(looperLocks==1); --looperLocks; clock_us+=1; }
    status_t SetViewOverlay(const BBitmap*,BRect,BRect,rgb_color*,int,int){
        clock_us+=17;return overlay_ok?B_OK:-1;
    }
    void SetLowColor(rgb_color){}
    void FillRect(BRect,int=0){clock_us+=2;}
    void Sync(){clock_us+=2;}
    void _SetOverlayMode(bool on){fOverlayMode=on;}
    void ClearViewOverlay(){}
    void SetViewColor(int){}
    void _LayoutSubtitle(){clock_us+=11;}
    void Invalidate(BRect){clock_us+=13;++invalidations;}
    void _DrawBitmap(const BBitmap*){clock_us+=19;++draws;}
    void SetBitmap(const BBitmap*);
};
''' + method.group() + r'''
int main(){
    BBitmap ordinary, overlay; overlay.flags=B_BITMAP_WILL_OVERLAY;
    {
        VideoView off;
        off.SetBitmap(&ordinary);
        off.SetBitmap(nullptr);
        assert(reads==0 && off.draws==1);
        off.fLabViewStats.Report(); // must emit nothing
    }
    marker=true;
    VideoView on;
    on.SetBitmap(nullptr);
    on.looper_ok=false;on.SetBitmap(&ordinary);on.looper_ok=true;
    on.bitmap_ok=false;on.SetBitmap(&ordinary);on.bitmap_ok=true;
    on.SetBitmap(&ordinary);
    on.fSubtitleChanged=true;on.SetBitmap(&ordinary);on.fSubtitleChanged=false;
    on.SetBitmap(&overlay);
    assert(on.draws==1 && on.invalidations==1 && on.fOverlayMode);
    assert(on.looperLocks==0 && on.bitmapLocks==0);
    on.fLabViewStats.Report();
    return 0;
}
'''
        with tempfile.TemporaryDirectory() as d:
            p=Path(d);(p/"OS.h").write_text(os_header);(p/"test.cpp").write_text(source)
            subprocess.run(["c++","-std=c++11","-Wall","-Wextra","-Werror","-I",d,"-I",str(app),str(p/"test.cpp"),"-o",str(p/"test")],check=True)
            result=subprocess.run([str(p/"test")],check=True,capture_output=True,text=True)
        lines=[l for l in result.stderr.splitlines() if l.startswith("LAB_VIDEO_VIEW ")]
        self.assertEqual(len(lines),1)
        fields={k:int(v) for k,v in (item.split("=") for item in lines[0].split()[1:])}
        self.assertEqual(fields["calls"],6)
        for name in ("null","looper_fail","bitmap_fail","overlay","invalidate","draw"):
            self.assertEqual(fields[name],1)
        self.assertEqual(fields["update_us"],18)
        self.assertEqual(fields["looper_us"],25)
        self.assertEqual(fields["bitmap_us"],28)
        self.assertEqual(fields["overlay_us"],20021)
        self.assertEqual(fields["invalidate_us"],24)
        self.assertEqual(fields["draw_us"],19)
        self.assertGreaterEqual(fields["total_us"],sum(fields[k] for k in ("update_us","looper_us","bitmap_us","overlay_us","invalidate_us","draw_us")))
