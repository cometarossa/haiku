// AI-assisted independent Haiku research fork. MIT.
// Offscreen app_server drawing and synchronization, verify every RGB pixel.
#include <Application.h>
#include <Bitmap.h>
#include <View.h>
#include <OS.h>
#include <cstdio>
#include <cstdlib>

static const int kSide = 256, kTile = 16, kPasses = 8;
static rgb_color Color(int x, int y, int pass)
{
    return rgb_color{uint8(x*13+pass*17),uint8(y*11+pass*23),
        uint8((x+y)*7+pass*31),255};
}
int main(int argc,char** argv)
{
    if(argc!=2)return 2;
    int batch=atoi(argv[1]);
    if(batch!=1&&batch!=64&&batch!=2048)return 2;
    BApplication app("application/x-vnd.cometarossa-draw-sync-lab");
    if(app.InitCheck()!=B_OK)return 3;
    BRect bounds(0,0,kSide-1,kSide-1);
    BBitmap bitmap(bounds,B_BITMAP_ACCEPTS_VIEWS,B_RGB32);
    if(bitmap.InitCheck()!=B_OK||!bitmap.Lock())return 4;
    BView* view=new BView(bounds,"offscreen",B_FOLLOW_NONE,0);
    bitmap.AddChild(view);
    view->SetDrawingMode(B_OP_COPY);
    view->Sync();
    int commands=0,syncs=0;
    bigtime_t start=system_time();
    for(int p=0;p<kPasses;++p)
        for(int y=0;y<kSide/kTile;++y)
            for(int x=0;x<kSide/kTile;++x){
                view->SetHighColor(Color(x,y,p));
                view->FillRect(BRect(x*kTile,y*kTile,
                    (x+1)*kTile-1,(y+1)*kTile-1));
                ++commands;
                if(commands%batch==0){view->Sync();++syncs;}
            }
    if(commands%batch){view->Sync();++syncs;}
    bigtime_t elapsed=system_time()-start;
    bitmap.Unlock();
    int checked=0,errors=0;
    if(bitmap.BytesPerRow()<4*kSide||bitmap.BitsLength()<size_t(bitmap.BytesPerRow())*kSide
        ||!bitmap.Bits())return 5;
    const uint8* bits=static_cast<const uint8*>(bitmap.Bits());
    for(int y=0;y<kSide;++y)
        for(int x=0;x<kSide;++x){
            const uint8* pixel=bits+y*bitmap.BytesPerRow()+4*x;
            rgb_color expected=Color(x/kTile,y/kTile,kPasses-1);
            if(pixel[0]!=expected.blue||pixel[1]!=expected.green||pixel[2]!=expected.red)
                ++errors;
            ++checked;
        }
    printf("%d,%d,%d,%lld,%d,%d\n",batch,commands,syncs,
        (long long)elapsed,checked,errors);
    return errors?1:0;
}
