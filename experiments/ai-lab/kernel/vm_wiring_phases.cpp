// AI-assisted independent Haiku research fork. MIT.
// Compare demand-paged and fully wired anonymous areas with phase barriers.
#include <OS.h>
#include <atomic>
#include <cstdio>
#include <cstdlib>
#include <cstring>

extern "C" int _kern_get_cpu();
extern "C" status_t _kern_get_thread_affinity(thread_id,void*,size_t);
extern "C" status_t _kern_set_thread_affinity(thread_id,const void*,size_t);
static const int kWorkers=4;
static const int kPhases=5;
struct Shared {
    std::atomic<int> phase{0}, ready{0}, done{0};
    std::atomic<bool> abort{false};
};
struct Worker {
    Shared* shared;
    int id,cpu,pages;
    bool readFirst, fullLock;
    bigtime_t elapsed[kPhases];
    int checked;
};
static uint64 Value(int id,int page)
{
    return (uint64(id+1)<<32)|uint32(page+1);
}
static status_t Run(void* data)
{
    Worker& w=*static_cast<Worker*>(data);
    Shared& s=*w.shared;
    uint32 mask[32]={uint32(1)<<w.cpu},actual[32]={};
    if(_kern_set_thread_affinity(0,mask,sizeof(mask))!=B_OK ||
        _kern_get_thread_affinity(0,actual,sizeof(actual))!=B_OK ||
        actual[0]!=mask[0])return B_ERROR;
    for(int i=0;i<100&&_kern_get_cpu()!=w.cpu;++i)snooze(1000);
    if(_kern_get_cpu()!=w.cpu)return B_ERROR;
    s.ready.fetch_add(1);
    void* address=NULL;
    area_id area=-1;
    constexpr size_t stride=B_PAGE_SIZE/sizeof(uint64);
    status_t status=B_OK;
    for(int phase=1;phase<=kPhases;++phase){
        while(s.phase.load()<phase&&!s.abort.load())snooze(1000);
        if(s.abort.load()){status=B_ERROR;break;}
        if(_kern_get_cpu()!=w.cpu){status=B_ERROR;break;}
        bigtime_t start=system_time();
        if(phase==1){
            area=create_area("lab phased anonymous",&address,B_ANY_ADDRESS,
                size_t(w.pages)*B_PAGE_SIZE,w.fullLock?B_FULL_LOCK:B_NO_LOCK,
                B_READ_AREA|B_WRITE_AREA);
            if(area<0)status=area;
        }else if(phase==5){
            status=delete_area(area);
            if(status==B_OK)area=-1;
        }else{
            volatile uint64* p=static_cast<volatile uint64*>(address);
            for(int i=0;i<w.pages;++i){
                size_t j=size_t(i)*stride;
                uint64 v=Value(w.id,i);
                if(phase==2&&w.readFirst){
                    if(p[j]!=0||p[j+stride-1]!=0){status=B_ERROR;break;}
                }else if(phase==2||(phase==3&&w.readFirst)){
                    p[j]=v;p[j+stride-1]=~v;
                }else{
                    if(p[j]!=v||p[j+stride-1]!=~v){status=B_ERROR;break;}
                    if(phase==4)++w.checked;
                }
            }
        }
        w.elapsed[phase-1]=system_time()-start;
        if(status!=B_OK||_kern_get_cpu()!=w.cpu){status=B_ERROR;break;}
        s.done.fetch_add(1);
    }
    if(area>=0)delete_area(area);
    if(status!=B_OK)s.abort.store(true);
    return status;
}
int main(int argc,char** argv)
{
    if(argc!=4)return 2;
    int cpus=atoi(argv[1]),pages=atoi(argv[2]);
    const bool readFirst=true;
    bool fullLock=strcmp(argv[3],"full")==0;
    if((cpus!=1&&cpus!=4)||(pages!=64&&pages!=256&&pages!=1024)||
        (!fullLock&&strcmp(argv[3],"demand")))return 2;
    Shared s;Worker w[kWorkers]={};thread_id ids[kWorkers];
    int started=0,errors=0;
    for(int i=0;i<kWorkers;++i){
        w[i]={&s,i,i%cpus,pages,readFirst,fullLock,{},0};
        thread_id id=spawn_thread(Run,"lab phased page worker",B_NORMAL_PRIORITY,&w[i]);
        if(id<0){++errors;break;}
        if(resume_thread(id)!=B_OK){kill_thread(id);wait_for_thread(id,NULL);++errors;break;}
        ids[started++]=id;
    }
    bigtime_t deadline=system_time()+2000000;
    while(s.ready.load()<kWorkers&&!s.abort.load()&&system_time()<deadline)snooze(1000);
    if(s.ready.load()!=kWorkers||started!=kWorkers){++errors;s.abort.store(true);}
    for(int phase=1;phase<=kPhases&&!s.abort.load();++phase){
        s.phase.store(phase);
        deadline=system_time()+15000000;
        while(s.done.load()<phase*kWorkers&&!s.abort.load()&&system_time()<deadline)snooze(1000);
        if(s.done.load()!=phase*kWorkers){++errors;s.abort.store(true);}
    }
    for(int i=0;i<started;++i){
        status_t result=B_ERROR;
        if(wait_for_thread_etc(ids[i],B_RELATIVE_TIMEOUT,3000000,&result)!=B_OK){
            kill_thread(ids[i]);wait_for_thread(ids[i],NULL);++errors;
        }else if(result!=B_OK)++errors;
    }
    if(errors||s.abort.load())return 3;
    for(int i=0;i<kWorkers;++i){
        if(w[i].checked!=pages)return 4;
        printf("%d,%d,%s,%d,%d,%lld,%lld,%lld,%lld,%lld,%d\n",
            cpus,pages,argv[3],i,w[i].cpu,(long long)w[i].elapsed[0],
            (long long)w[i].elapsed[1],(long long)w[i].elapsed[2],
            (long long)w[i].elapsed[3],(long long)w[i].elapsed[4],w[i].checked);
    }
    return 0;
}
