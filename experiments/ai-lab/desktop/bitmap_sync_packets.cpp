// AI-assisted independent Haiku research fork. MIT.
// Verify synchronous bitmap lifetime and pixels in/out of a transaction.
#include <Application.h>
#include <Bitmap.h>
#include <View.h>
#include <Window.h>
#include <OS.h>
#include <cstdio>
#include <cstdlib>
#include <cstring>
#include <set>

static const int kSide=256,kTile=16,kPasses=4;
static rgb_color Color(int x,int y,int pass)
{
    return rgb_color{uint8(x*13+pass*17),uint8(y*11+pass*23),
        uint8((x+y)*7+pass*31),255};
}
// Discover the newly created offscreen server port rather than relying
// on the first port with a non-unique name.
static std::set<port_id> OffscreenPorts()
{
    std::set<port_id> ports;
    team_info team;
    int32 teamCookie=0;
    while(get_next_team_info(&teamCookie,&team)==B_OK){
        int32 cookie=0;
        port_info info;
        while(get_next_port_info(team.team,&cookie,&info)==B_OK)
            if(strcmp(info.name,"offscreen")==0)ports.insert(info.port);
    }
    return ports;
}
int main(int argc,char** argv)
{
    if(argc!=2)return 2;
    bool transaction=strcmp(argv[1],"transaction")==0;
    if(!transaction&&strcmp(argv[1],"direct"))return 2;
    BApplication app("application/x-vnd.cometarossa-bitmap-sync-lab");
    if(app.InitCheck()!=B_OK)return 3;
    BRect bounds(0,0,kSide-1,kSide-1),tile(0,0,kTile-1,kTile-1);
    const std::set<port_id> before=OffscreenPorts();
    BBitmap dest(bounds,B_BITMAP_ACCEPTS_VIEWS,B_RGB32);
    BBitmap source(tile,B_RGB32);
    if(dest.InitCheck()!=B_OK||source.InitCheck()!=B_OK||!dest.Lock())return 4;
    if(!source.Bits()||source.BytesPerRow()<kTile*4||
        source.BitsLength()<size_t(source.BytesPerRow())*kTile)return 5;
    BView* view=new BView(bounds,"offscreen",B_FOLLOW_NONE,0);
    dest.AddChild(view);
    BWindow* owner=view->Window();
    if(!owner)return 6;
    if(transaction)owner->BeginViewTransaction();
    else owner->EndViewTransaction();
    if(owner->InViewTransaction()!=transaction)return 7;
    view->SetDrawingMode(B_OP_COPY);
    view->Sync();
    port_id server=-1;
    for(port_id p:OffscreenPorts()){
        if(before.count(p))continue;
        if(server>=0)return 9;
        server=p;
    }
    port_info initial,final;
    if(server<0||get_port_info(server,&initial)!=B_OK||initial.queue_count!=0)
        return 10;
    int draws=0;
    bigtime_t start=system_time();
    for(int p=0;p<kPasses;++p)
        for(int y=0;y<kSide/kTile;++y)
            for(int x=0;x<kSide/kTile;++x){
                rgb_color c=Color(x,y,p);
                uint8* bits=static_cast<uint8*>(source.Bits());
                for(int sy=0;sy<kTile;++sy)
                    for(int sx=0;sx<kTile;++sx){
                        uint8* pixel=bits+sy*source.BytesPerRow()+4*sx;
                        pixel[0]=c.blue;pixel[1]=c.green;pixel[2]=c.red;pixel[3]=255;
                    }
                BPoint where(x*kTile,y*kTile);
                BRect dst=tile.OffsetToCopy(where);
                switch((x+y)%4){
                    case 0:view->DrawBitmap(&source,where);break;
                    case 1:view->DrawBitmap(&source,tile,dst);break;
                    case 2:view->DrawBitmap(&source,tile,dst,0);break;
                    case 3:view->DrawTiledBitmap(&source,dst,B_ORIGIN);break;
                }
                // Reuse source immediately after synchronous return.
                memset(source.Bits(),0,source.BitsLength());
                ++draws;
            }
    bigtime_t elapsed=system_time()-start;
    if(get_port_info(server,&final)!=B_OK||final.team!=initial.team
        ||final.queue_count!=0||final.total_count<initial.total_count)return 11;
    int packets=final.total_count-initial.total_count;
    // Existing invalid-input calls must retain the sync barrier.
    view->DrawBitmap(NULL,BPoint(0,0));
    view->DrawBitmap(&source,BRect(2,2,1,1),tile);
    view->DrawTiledBitmap(NULL,tile,B_ORIGIN);
    if(transaction)owner->EndViewTransaction();
    dest.Unlock();
    if(!dest.Bits()||dest.BytesPerRow()<kSide*4||
        dest.BitsLength()<size_t(dest.BytesPerRow())*kSide)return 8;
    const uint8* bits=static_cast<const uint8*>(dest.Bits());
    int checked=0,errors=0;
    for(int y=0;y<kSide;++y)
        for(int x=0;x<kSide;++x){
            const uint8* pixel=bits+y*dest.BytesPerRow()+4*x;
            rgb_color c=Color(x/kTile,y/kTile,kPasses-1);
            if(pixel[0]!=c.blue||pixel[1]!=c.green||pixel[2]!=c.red)++errors;
            ++checked;
        }
    printf("%s,%d,%lld,%d,%d,%d\n",argv[1],draws,(long long)elapsed,checked,errors,packets);
    return errors?1:0;
}
