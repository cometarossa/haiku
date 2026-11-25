// AI-assisted independent research fork. MIT.
// Verify eligible and excluded bitmap allocations; partial RGB32 draw
// must preserve all untouched pixels, including another live allocation.
#include <Application.h>
#include <Bitmap.h>
#include <View.h>
#include <cstdio>
#include <cstring>

static bool CheckBytes(BBitmap& b, uint8 value)
{
    if(b.InitCheck()!=B_OK || !b.Bits() || b.BitsLength()<=0)return false;
    const uint8* p=static_cast<const uint8*>(b.Bits());
    for(int32 i=0;i<b.BitsLength();++i)if(p[i]!=value)return false;
    return true;
}

static bool Check(const char* name,int w,int h,uint32 flags,color_space space)
{
    BRect bounds(0,0,w-1,h-1);
    BBitmap b(bounds,flags,space);
    if(b.InitCheck()!=B_OK||!b.Bits()||b.BitsLength()<=0)return false;
    const bool clear=(flags&B_BITMAP_CLEAR_TO_WHITE)!=0;
    if(clear&&!CheckBytes(b,255))return false;
    int32 initial=clear?b.BitsLength():0;
    int32 pixels=0;
    if(space==B_RGB32&&(flags&B_BITMAP_ACCEPTS_VIEWS)){
        if(!b.Lock())return false;
        if(!clear)memset(b.Bits(),0x39,b.BitsLength());
        BView* view=new BView(bounds,"partial",B_FOLLOW_NONE,0);
        b.AddChild(view);
        view->SetDrawingMode(B_OP_COPY);
        view->SetHighColor(0x12,0x34,0x56,255);
        view->FillRect(BRect(0,0,15,15));
        view->Sync();
        b.Unlock();
        const uint8* p=static_cast<const uint8*>(b.Bits());
        if(b.BytesPerRow()<w*4||b.BitsLength()<b.BytesPerRow()*h)return false;
        for(int y=0;y<h;++y)
            for(int x=0;x<w;++x){
                const uint8* q=p+y*b.BytesPerRow()+4*x;
                bool inside=x<16&&y<16;
                uint8 untouched=clear?255:0x39;
                if(q[0]!=(inside?0x56:untouched)||
                   q[1]!=(inside?0x34:untouched)||
                   q[2]!=(inside?0x12:untouched))return false;
                ++pixels;
            }
    }
    printf("%s,%ld,%ld,%ld,0\n",name,(long)b.BitsLength(),(long)initial,(long)pixels);
    return true;
}

int main(int argc,char** argv)
{
    if(argc!=2)return 2;
    bool lab=!strcmp(argv[1],"lab");
    if(!lab&&strcmp(argv[1],"ordinary"))return 2;
    BApplication app(lab?"application/x-vnd.cometarossa-v11-eligibility":
        "application/x-vnd.cometarossa-ordinary-eligibility");
    if(app.InitCheck()!=B_OK)return 3;
    const uint32 white=B_BITMAP_ACCEPTS_VIEWS|B_BITMAP_CLEAR_TO_WHITE;
    // Keep a small, noneligible bitmap live and verify its sentinel bytes
    // after all subsequent allocations/draws. Not proof of shared page layout.
    BBitmap neighbor(BRect(0,0,31,31),uint32(0),B_RGB32);
    if(neighbor.InitCheck()!=B_OK||!neighbor.Bits())return 4;
    memset(neighbor.Bits(),0x6d,neighbor.BitsLength());
    if(!Check("eligible",256,256,white,B_RGB32)||
        !Check("boundary",512,512,white,B_RGB32)||
        !Check("oversize",1024,512,white,B_RGB32)||
        !Check("no-clear",256,256,B_BITMAP_ACCEPTS_VIEWS,B_RGB32)||
        !Check("rgb16",256,256,white,B_RGB16)||
        !Check("no-views",256,256,B_BITMAP_CLEAR_TO_WHITE,B_RGB32)||
        !CheckBytes(neighbor,0x6d))return 5;
    printf("neighbor,%ld,%ld,0,0\n",(long)neighbor.BitsLength(),(long)neighbor.BitsLength());
    return 0;
}
