// AI-assisted independent Haiku research fork. MIT.
// V11: explicit white initialization, constructor and render timings.
#include <Application.h>
#include <Bitmap.h>
#include <View.h>
#include <OS.h>
#include <cstdio>
#include <cstdlib>
#include <unistd.h>
#include <cstring>
#include <cerrno>
#include <poll.h>
#include <signal.h>
#include <sys/wait.h>

static const int kSide=256,kTile=16,kTotalPasses=16,kTotalDraws=4096;
struct Job {
    int id,batch,passes;
    int readyFd,goFd;
    sem_id ready,go;
    bigtime_t start,end;
    int checked,errors;
    bigtime_t setup_start,ready_time;
    int white_errors;
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
    j.setup_start=system_time();
    BBitmap bitmap(bounds,B_BITMAP_ACCEPTS_VIEWS | B_BITMAP_CLEAR_TO_WHITE,B_RGB32);
    if(bitmap.InitCheck()!=B_OK||!bitmap.Lock())return B_ERROR;
    if(!bitmap.Bits() || bitmap.BitsLength()!=size_t(kSide*kSide*4))return B_ERROR;
    const uint8* white=static_cast<const uint8*>(bitmap.Bits());
    for(size_t i=0;i<bitmap.BitsLength();++i)if(white[i]!=255)++j.white_errors;
    if(j.white_errors)return B_ERROR;
    BView* view=new BView(bounds,"offscreen",B_FOLLOW_NONE,0);
    bitmap.AddChild(view);
    view->SetDrawingMode(B_OP_COPY);
    view->Sync();
    j.ready_time=system_time();
    if(j.readyFd>=0){
        char token;
        if(write(j.readyFd,"R",1)!=1||read(j.goFd,&token,1)!=1||token!='G')
            return B_ERROR;
    }else if(release_sem(j.ready)!=B_OK||
        acquire_sem_etc(j.go,1,B_RELATIVE_TIMEOUT,10000000)!=B_OK)
        return B_ERROR;
    int draws=0;
    j.start=system_time();
    for(int p=0;p<j.passes;++p)
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
            rgb_color c=Color(j.id,x/kTile,y/kTile,j.passes-1);
            if(pixel[0]!=c.blue||pixel[1]!=c.green||pixel[2]!=c.red)++j.errors;
            ++j.checked;
        }
    return j.errors?B_ERROR:B_OK;
}
static bool Valid(const Job& j,int n,int batch,int id)
{
    return j.id==id&&j.batch==batch&&j.passes==kTotalPasses/n
        &&j.start>0&&j.end>j.start&&j.checked==65536&&!j.errors
        &&j.setup_start>0&&j.ready_time>=j.setup_start&&j.start>=j.ready_time
        &&!j.white_errors;
}
static int Report(const char* mode,Job* jobs,int n,int batch)
{
    bigtime_t first=jobs[0].start,last=jobs[0].end,setup=jobs[0].setup_start;
    for(int i=0;i<n;++i){
        if(!Valid(jobs[i],n,batch,i))return 8;
        if(jobs[i].start<first)first=jobs[i].start;
        if(jobs[i].end>last)last=jobs[i].end;
    }
    for(int i=0;i<n;++i){
        Job& j=jobs[i];
        printf("%s,%d,%d,%d,%d,%lld,%lld,%lld,%d,%d,%lld,%lld,%d\n",mode,n,batch,i,kTotalDraws/n,
            (long long)(j.start-first),(long long)(j.end-first),
            (long long)(last-first),j.checked,j.errors,
            (long long)(j.ready_time-j.setup_start),
            (long long)(last-setup),j.white_errors);
    }
    return 0;
}
static int Threads(int n,int batch)
{
    BApplication app("application/x-vnd.cometarossa-v11-threads");
    if(app.InitCheck()!=B_OK)return 3;
    sem_id ready=create_sem(0,"draw ready"),go=create_sem(0,"draw go");
    if(ready<0||go<0)return 4;
    Job jobs[4]={};thread_id threads[4];
    for(int i=0;i<n;++i){
        jobs[i]={i,batch,kTotalPasses/n,-1,-1,ready,go,0,0,0,0,0,0,0};
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
    return failures?8:Report("threads",jobs,n,batch);
}
static bool ReadBounded(int fd,void* buffer,size_t bytes,bigtime_t deadline)
{
    char* p=static_cast<char*>(buffer);
    while(bytes){
        bigtime_t remaining=deadline-system_time();
        if(remaining<=0)return false;
        pollfd f={fd,POLLIN,0};
        int result=poll(&f,1,int((remaining+999)/1000));
        if(result<0&&errno==EINTR)continue;
        if(result<=0)return false;
        ssize_t n=read(fd,p,bytes);
        if(n<0&&errno==EINTR)continue;
        if(n<=0)return false;
        p+=n;bytes-=n;
    }
    return true;
}
static int Teams(int n,int batch)
{
    int ready[2],go[2],out[2];
    if(pipe(ready)||pipe(go)||pipe(out))return 9;
    pid_t children[4];int count=0;bool ok=true;
    // Fork before any BApplication or GUI threads exist.
    for(int i=0;i<n;++i){
        pid_t pid=fork();
        if(pid<0){ok=false;break;}
        if(pid==0){
            close(ready[0]);close(go[1]);close(out[0]);
            Job j={i,batch,kTotalPasses/n,ready[1],go[0],-1,-1,0,0,0,0,0,0,0};
            char signature[96];
            snprintf(signature,sizeof(signature),"application/x-vnd.cometarossa-v11-%ld",(long)getpid());
            {
                BApplication app(signature);
                if(app.InitCheck()!=B_OK||Draw(&j)!=B_OK||!Valid(j,n,batch,i))
                    _exit(10);
            }
            if(write(out[1],&j,sizeof(j))!=sizeof(j))_exit(11);
            _exit(0);
        }
        children[count++]=pid;
    }
    close(ready[1]);close(go[0]);close(out[1]);
    char tokens[4];bigtime_t deadline=system_time()+20000000;
    if(ok)ok=ReadBounded(ready[0],tokens,n,deadline);
    if(ok)ok=write(go[1],"GGGG",n)==n;
    close(ready[0]);close(go[1]);
    Job jobs[4]={};
    for(int i=0;i<n&&ok;++i){
        Job j={};ok=ReadBounded(out[0],&j,sizeof(j),deadline);
        if(!ok)break;
        if(j.id<0||j.id>=n||jobs[j.id].checked||!Valid(j,n,batch,j.id)){
            ok=false;break;
        }
        jobs[j.id]=j;
    }
    close(out[0]);
    if(!ok)for(int i=0;i<count;++i)kill(children[i],SIGKILL);
    for(int i=0;i<count;++i){
        int status=0;pid_t rc;
        do{rc=waitpid(children[i],&status,0);}while(rc<0&&errno==EINTR);
        if(rc!=children[i]||!WIFEXITED(status)||WEXITSTATUS(status)!=0)ok=false;
    }
    return ok&&count==n?Report("teams",jobs,n,batch):12;
}
int main(int argc,char** argv)
{
    if(argc!=4)return 2;
    int n=atoi(argv[2]),batch=atoi(argv[3]);
    if((n!=1&&n!=2&&n!=4)||(batch!=1&&batch!=64&&batch!=1024))return 2;
    if(!strcmp(argv[1],"threads"))return Threads(n,batch);
    if(!strcmp(argv[1],"teams"))return Teams(n,batch);
    return 2;
}
