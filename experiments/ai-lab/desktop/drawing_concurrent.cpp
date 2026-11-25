// AI-assisted independent Haiku research fork. MIT.
// Independent offscreen surfaces in one team, common start barrier.
#include <Application.h>
#include <Bitmap.h>
#include <View.h>
#include <OS.h>
#include <cstdio>
#include <cstdlib>
#include <unistd.h>

static const int kSide=256,kTile=16,kPasses=4,kDraws=1024;
struct Job {
    int id,batch;
    sem_id ready,go;
    bigtime_t start,end;
    int checked,errors;
};
static rgb_color Color(int id,int x,int y,int pass)
{
    return rgb_color{uint8(x*13+pass*17+id*29),
        uint8(y*11+pass*23+id*37),uint8((x+y)*7+pass*31+id*41),255};
}
static status_t Draw(void* arg)
{
    Job& j=*static_cast<Job*>(arg);
    BRect bounds(0,0,kSide-1,kSide-1);
    BBitmap bitmap(bounds,B_BITMAP_ACCEPTS_VIEWS,B_RGB32);
    if(bitmap.InitCheck()!=B_OK||!bitmap.Lock())return B_ERROR;
    BView* view=new BView(bounds,"offscreen",B_FOLLOW_NONE,0);
    bitmap.AddChild(view);
    view->SetDrawingMode(B_OP_COPY);
    view->Sync();
    if(release_sem(j.ready)!=B_OK||
        acquire_sem_etc(j.go,1,B_RELATIVE_TIMEOUT,10000000)!=B_OK)
        return B_ERROR;
    int draws=0;
    j.start=system_time();
    for(int p=0;p<kPasses;++p)
        for(int y=0;y<kSide/kTile;++y)
            for(int x=0;x<kSide/kTile;++x){
                view->SetHighColor(Color(j.id,x,y,p));
                view->FillRect(BRect(x*kTile,y*kTile,
                    (x+1)*kTile-1,(y+1)*kTile-1));
                if(++draws%j.batch==0)view->Sync();
            }
    if(draws%j.batch)view->Sync();
    j.end=system_time();
    bitmap.Unlock();
    if(!bitmap.Bits()||bitmap.BytesPerRow()<4*kSide||
        bitmap.BitsLength()<size_t(bitmap.BytesPerRow())*kSide)return B_ERROR;
    const uint8* bits=static_cast<const uint8*>(bitmap.Bits());
    for(int y=0;y<kSide;++y)
        for(int x=0;x<kSide;++x){
            const uint8* pixel=bits+y*bitmap.BytesPerRow()+4*x;
            rgb_color c=Color(j.id,x/kTile,y/kTile,kPasses-1);
            if(pixel[0]!=c.blue||pixel[1]!=c.green||pixel[2]!=c.red)++j.errors;
            ++j.checked;
        }
    return j.errors?B_ERROR:B_OK;
}
int main(int argc,char** argv)
{
    if(argc!=3)return 2;
    int n=atoi(argv[1]),batch=atoi(argv[2]);
    if((n!=1&&n!=2&&n!=4)||(batch!=1&&batch!=64&&batch!=1024))return 2;
    BApplication app("application/x-vnd.cometarossa-draw-concurrent-lab");
    if(app.InitCheck()!=B_OK)return 3;
    sem_id ready=create_sem(0,"draw ready"),go=create_sem(0,"draw go");
    if(ready<0||go<0)return 4;
    Job jobs[4]={};thread_id threads[4];
    for(int i=0;i<n;++i){
        jobs[i]={i,batch,ready,go,0,0,0,0};
        threads[i]=spawn_thread(Draw,"draw surface",B_NORMAL_PRIORITY,&jobs[i]);
        if(threads[i]<0||resume_thread(threads[i])!=B_OK)_exit(5);
    }
    if(acquire_sem_etc(ready,n,B_RELATIVE_TIMEOUT,10000000)!=B_OK||
        release_sem_etc(go,n,0)!=B_OK)_exit(6);
    bigtime_t deadline=system_time()+20000000;
    int failures=0;
    for(int i=0;i<n;++i){
        status_t status=B_ERROR;
        if(wait_for_thread_etc(threads[i],B_ABSOLUTE_TIMEOUT,deadline,&status)!=B_OK)
            _exit(7);
        if(status!=B_OK)++failures;
    }
    delete_sem(ready);delete_sem(go);
    bigtime_t first=jobs[0].start,last=jobs[0].end;
    for(int i=0;i<n;++i){
        Job& j=jobs[i];
        if(j.start<=0||j.end<j.start||j.checked!=65536||j.errors)++failures;
        if(j.start<first)first=j.start;
        if(j.end>last)last=j.end;
    }
    for(int i=0;i<n;++i){
        Job& j=jobs[i];
        printf("%d,%d,%d,%d,%lld,%lld,%lld,%d,%d\n",n,batch,i,kDraws,
            (long long)(j.start-first),(long long)(j.end-first),
            (long long)(last-first),j.checked,j.errors);
    }
    return failures?1:0;
}
