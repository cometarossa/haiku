// AI-assisted independent Haiku research fork. MIT.
// Bounded CPU work, equal-priority workers and common measurement interval.
#include <OS.h>
#include <scheduler.h>
#include <atomic>
#include <cstdio>
#include <cstdlib>
extern "C" int _kern_get_cpu();
extern "C" status_t _kern_set_thread_affinity(thread_id,const void*,size_t);
extern "C" status_t _kern_get_thread_affinity(thread_id,void*,size_t);
static const int kWorkers=4;
static const bigtime_t kDuration=1000000;
struct Shared {
    std::atomic<int> ready{0};
    std::atomic<bigtime_t> start{0};
    std::atomic<bool> abort{false};
};
struct Worker {
    Shared* shared;
    int cpu;
    uint64 batches;
    uint64 digest;
    bigtime_t begin,end;
};
static status_t Run(void* data)
{
    Worker& w=*static_cast<Worker*>(data);
    uint32 mask[32]={},actual[32]={};
    mask[w.cpu/32]=uint32(1)<<(w.cpu%32);
    if(_kern_set_thread_affinity(0,mask,sizeof(mask))!=B_OK
        || _kern_get_thread_affinity(0,actual,sizeof(actual))!=B_OK
        || actual[0]!=mask[0]) { fprintf(stderr,"affinity failed cpu=%d\n",w.cpu); return B_ERROR; }
    w.shared->ready.fetch_add(1);
    bigtime_t start;
    while((start=w.shared->start.load())==0){
        if(w.shared->abort.load()) return B_ERROR;
        snooze(1000);
    }
    while(system_time()<start){
        status_t s=snooze_until(start,B_SYSTEM_TIMEBASE);
        if(s!=B_OK && s!=B_INTERRUPTED && system_time()<start){
            fprintf(stderr,"sleep failed cpu=%d status=%ld\n",w.cpu,(long)s);
            return s;
        }
    }
    w.begin=system_time();
    uint64 x=1;
    while(!w.shared->abort.load() && system_time()<start+kDuration){
        if(_kern_get_cpu()!=w.cpu){fprintf(stderr,"wrong cpu expected=%d\n",w.cpu);return B_ERROR;}
        for(int j=0;j<1024;++j) {
            x ^= x<<13; x ^= x>>7; x ^= x<<17;
        }
        ++w.batches;
    }
    w.end=system_time();
    w.digest=x;
    return w.batches>0?B_OK:B_ERROR;
}
int main(int argc,char** argv)
{
    if(argc!=2) return 2;
    int cpus=atoi(argv[1]);
    if(cpus!=1 && cpus!=4) return 2;
    if(get_scheduler_mode()!=SCHEDULER_MODE_LOW_LATENCY) return 3;
    Shared shared;
    Worker workers[kWorkers]={};
    thread_id ids[kWorkers];
    int started=0, errors=0;
    for(int i=0;i<kWorkers;++i){
        workers[i].shared=&shared;workers[i].cpu=i%cpus;
        thread_id id=spawn_thread(Run,"lab equal priority work",B_NORMAL_PRIORITY,&workers[i]);
        if(id<0){++errors;break;}
        if(resume_thread(id)!=B_OK){kill_thread(id);wait_for_thread(id,NULL);++errors;break;}
        ids[started++]=id;
    }
    for(int i=0;i<500 && shared.ready.load()<started;++i) snooze(1000);
    if(shared.ready.load()!=kWorkers || started!=kWorkers) ++errors;
    if(errors) shared.abort.store(true);
    shared.start.store(system_time()+50000);
    for(int i=0;i<started;++i){
        status_t result=B_ERROR;
        if(wait_for_thread_etc(ids[i],B_RELATIVE_TIMEOUT,4000000,&result)!=B_OK){
            shared.abort.store(true);kill_thread(ids[i]);wait_for_thread(ids[i],NULL);++errors;
        }else if(result!=B_OK){fprintf(stderr,"worker %d returned %ld\n",i,(long)result);++errors;}
    }
    if(errors){fprintf(stderr,"errors=%d ready=%d started=%d\n",errors,shared.ready.load(),started);return 4;}
    for(int i=0;i<kWorkers;++i)
        printf("%d,%d,%d,%llu,%llu,%lld,%lld\n",cpus,i,workers[i].cpu,
            (unsigned long long)workers[i].batches,(unsigned long long)workers[i].digest,
            (long long)(workers[i].begin-shared.start.load()),
            (long long)(workers[i].end-shared.start.load()));
    return 0;
}
