// AI-assisted independent Haiku research fork. MIT.
// Independent teams or threads, identical page lifecycle and placement.
#include <OS.h>
#include <atomic>
#include <cstdio>
#include <cstdlib>
#include <cstring>
#include <unistd.h>
#include <sys/wait.h>
#include <poll.h>
#include <signal.h>
#include <cerrno>
extern "C" int _kern_get_cpu();
extern "C" status_t _kern_get_thread_affinity(thread_id,void*,size_t);
extern "C" status_t _kern_set_thread_affinity(thread_id,const void*,size_t);
struct Result {
    int worker, pages, cpu;
    std::atomic<int>* ready;
    std::atomic<bool>* start;
    std::atomic<bool>* abort;
    bigtime_t create, touch, warm, clone, verify, destroy;
    int checked;
    int readyFd, startFd;
};
static uint64 Pattern(int worker,int page)
{
    return (uint64(worker+1)<<32)|uint32(page+1);
}
static status_t Work(void* arg)
{
    Result& r=*static_cast<Result*>(arg);
    uint32 mask[32]={uint32(1)<<r.cpu},actual[32]={};
    if(_kern_set_thread_affinity(0,mask,sizeof(mask))!=B_OK
        || _kern_get_thread_affinity(0,actual,sizeof(actual))!=B_OK
        || actual[0]!=mask[0]) return B_ERROR;
    for(int i=0;i<100&&_kern_get_cpu()!=r.cpu;++i)snooze(1000);
    if(_kern_get_cpu()!=r.cpu)return B_ERROR;
    if(r.readyFd>=0){
        char token='R';
        if(write(r.readyFd,&token,1)!=1 || read(r.startFd,&token,1)!=1
            || token!='G')return B_ERROR;
    }else{
    r.ready->fetch_add(1);
    while(!r.start->load()){
        if(r.abort->load())return B_ERROR;
        snooze(1000);
    }
    if(r.abort->load())return B_ERROR;
    }
    void* address=NULL;
    size_t bytes=size_t(r.pages)*B_PAGE_SIZE;
    bigtime_t t=system_time();
    area_id a=create_area("lab anonymous pages",&address,B_ANY_ADDRESS,
        bytes,B_NO_LOCK,B_READ_AREA|B_WRITE_AREA|B_CLONEABLE_AREA);
    r.create=system_time()-t;
    if(a<0)return a;
    status_t error=B_OK;
    area_id c=-1;
    void* alias=NULL;
    volatile uint64* p=static_cast<volatile uint64*>(address);
    constexpr size_t stride=B_PAGE_SIZE/sizeof(uint64);
    t=system_time();
    for(int i=0;i<r.pages;++i){
        size_t j=size_t(i)*stride;
        if(p[j]!=0||p[j+stride-1]!=0){error=B_ERROR;break;}
        p[j]=Pattern(r.worker,i);
        p[j+stride-1]=~Pattern(r.worker,i);
    }
    r.touch=system_time()-t;
    t=system_time();
    if(error==B_OK){
        for(int i=0;i<r.pages;++i){
            size_t j=size_t(i)*stride;
            if(p[j]!=Pattern(r.worker,i)||p[j+stride-1]!=~Pattern(r.worker,i)){
                error=B_ERROR;break;
            }
            p[j]=Pattern(r.worker,i);
        }
    }
    r.warm=system_time()-t;
    if(_kern_get_cpu()!=r.cpu)error=B_ERROR;
    if(error==B_OK){
        t=system_time();
        c=clone_area("lab alias",&alias,B_ANY_ADDRESS,B_READ_AREA|B_WRITE_AREA,a);
        r.clone=system_time()-t;
        if(c<0)error=c;
    }
    if(error==B_OK){
        volatile uint64* q=static_cast<volatile uint64*>(alias);
        t=system_time();
        for(int i=0;i<r.pages;++i){
            size_t j=size_t(i)*stride;
            if(q[j]!=Pattern(r.worker,i)||q[j+stride-1]!=~Pattern(r.worker,i)){
                error=B_ERROR;break;
            }
            q[j]^=uint64(0x55);
            if(p[j]!=(Pattern(r.worker,i)^uint64(0x55))){error=B_ERROR;break;}
            ++r.checked;
        }
        r.verify=system_time()-t;
        if(delete_area(a)!=B_OK)error=B_ERROR;
        else {
            a=-1;
            for(int i=0;i<r.pages;++i){
                size_t j=size_t(i)*stride;
                if(q[j]!=(Pattern(r.worker,i)^uint64(0x55))||
                    q[j+stride-1]!=~Pattern(r.worker,i)){error=B_ERROR;break;}
                ++r.checked;
            }
        }
    }
    t=system_time();
    if(c>=0&&delete_area(c)!=B_OK)error=B_ERROR;
    if(a>=0&&delete_area(a)!=B_OK)error=B_ERROR;
    r.destroy=system_time()-t;
    return error;
}
static int Threads(int pages,int cpus)
{
    const int n=4;
    std::atomic<int> ready{0};
    std::atomic<bool> start{false},abort{false};
    Result results[4]={};
    thread_id ids[4];
    int started=0,errors=0;
    for(int i=0;i<n;++i){
        results[i]={i,pages,i%cpus,&ready,&start,&abort,0,0,0,0,0,0,0,-1,-1};
        thread_id id=spawn_thread(Work,"lab VM lifecycle",B_NORMAL_PRIORITY,&results[i]);
        if(id<0){++errors;break;}
        if(resume_thread(id)!=B_OK){kill_thread(id);wait_for_thread(id,NULL);++errors;break;}
        ids[started++]=id;
    }
    for(int i=0;i<500&&ready.load()<n;++i)snooze(1000);
    if(ready.load()!=n||started!=n){++errors;abort.store(true);}
    start.store(true);
    for(int i=0;i<started;++i){
        status_t status=B_ERROR;
        if(wait_for_thread_etc(ids[i],B_RELATIVE_TIMEOUT,20000000,&status)!=B_OK){
            fprintf(stderr,"worker %d wait timeout or error\n",i);
            abort.store(true);kill_thread(ids[i]);wait_for_thread(ids[i],NULL);++errors;
        }else if(status!=B_OK){fprintf(stderr,"worker %d status %ld\n",i,(long)status);++errors;}
    }
    if(errors)return 3;
    for(int i=0;i<n;++i){
        Result& r=results[i];
        if(r.checked!=2*pages)return 4;
        printf("threads,%d,%d,%d,%d,%d,%lld,%lld,%lld,%lld,%lld,%lld,%d\n",n,pages,cpus,i,r.cpu,
            (long long)r.create,(long long)r.touch,(long long)r.warm,(long long)r.clone,
            (long long)r.verify,(long long)r.destroy,r.checked);
    }
    return 0;
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
static int Teams(int pages,int cpus)
{
    int ready[2],start[2],out[2];
    if(pipe(ready)||pipe(start)||pipe(out))return 5;
    pid_t children[4];int count=0;
    bool ok=true;
    for(int i=0;i<4;++i){
        pid_t pid=fork();
        if(pid<0){ok=false;break;}
        if(pid==0){
            close(ready[0]);close(start[1]);close(out[0]);
            Result r={i,pages,i%cpus,NULL,NULL,NULL,0,0,0,0,0,0,0,ready[1],start[0]};
            status_t result=Work(&r);
            if(result!=B_OK || r.checked!=2*pages)_exit(6);
            if(write(out[1],&r,sizeof(r))!=sizeof(r))_exit(7);
            _exit(0);
        }
        children[count++]=pid;
    }
    close(ready[1]);close(start[0]);close(out[1]);
    char tokens[4];
    bigtime_t deadline=system_time()+20000000;
    if(ok)ok=ReadBounded(ready[0],tokens,4,deadline);
    if(ok)ok=write(start[1],"GGGG",4)==4;
    close(ready[0]);close(start[1]);
    Result results[4]={};
    for(int i=0;i<4&&ok;++i){
        Result r={};
        ok=ReadBounded(out[0],&r,sizeof(r),deadline);
        if(!ok)break;
        if(r.worker<0||r.worker>=4||results[r.worker].checked
            ||r.checked!=2*pages||r.cpu!=r.worker%cpus){ok=false;break;}
        results[r.worker]=r;
    }
    close(out[0]);
    if(!ok)for(int i=0;i<count;++i)kill(children[i],SIGKILL);
    for(int i=0;i<count;++i){
        int status=0;
        pid_t rc;
        do {rc=waitpid(children[i],&status,0);} while(rc<0&&errno==EINTR);
        if(rc!=children[i]||!WIFEXITED(status)||WEXITSTATUS(status)!=0)ok=false;
    }
    if(!ok||count!=4)return 8;
    for(int i=0;i<4;++i){
        Result& r=results[i];
        printf("teams,4,%d,%d,%d,%d,%lld,%lld,%lld,%lld,%lld,%lld,%d\n",
            pages,cpus,i,r.cpu,(long long)r.create,(long long)r.touch,
            (long long)r.warm,(long long)r.clone,(long long)r.verify,
            (long long)r.destroy,r.checked);
    }
    return 0;
}
int main(int argc,char** argv)
{
    if(argc!=4)return 2;
    int pages=atoi(argv[2]),cpus=atoi(argv[3]);
    if((pages!=64&&pages!=256&&pages!=1024)||(cpus!=1&&cpus!=4))return 2;
    if(!strcmp(argv[1],"threads"))return Threads(pages,cpus);
    if(!strcmp(argv[1],"teams"))return Teams(pages,cpus);
    return 2;
}
