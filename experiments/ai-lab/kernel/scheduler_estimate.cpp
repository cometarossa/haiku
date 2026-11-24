// AI-assisted independent Haiku research fork. MIT.
// Check the native latency estimate for a pinned thread with 0 or 2
// competing runnable normal-priority workers. No real-time priority.
#include <OS.h>
#include <scheduler.h>
#include <atomic>
#include <cstdio>
#include <cstdlib>
extern "C" int _kern_get_cpu();
extern "C" status_t _kern_set_thread_affinity(thread_id,const void*,size_t);
extern "C" status_t _kern_get_thread_affinity(thread_id,void*,size_t);
struct Load { std::atomic<bool> stop{false}; std::atomic<int> ready{0}; };
static bool Pin()
{
    uint32 mask[32]={1},actual[32]={};
    if(_kern_set_thread_affinity(0,mask,sizeof(mask))!=B_OK
        || _kern_get_thread_affinity(0,actual,sizeof(actual))!=B_OK
        || actual[0]!=1) return false;
    for(int i=0;i<100 && _kern_get_cpu()!=0;++i) snooze(1000);
    return _kern_get_cpu()==0;
}
static status_t Worker(void* data)
{
    Load& l=*static_cast<Load*>(data);
    if(!Pin()) return B_ERROR;
    l.ready.fetch_add(1);
    const bigtime_t end=system_time()+3000000;
    while(!l.stop.load() && system_time()<end) {
        volatile uint64 x=1;
        for(int i=0;i<1024;++i) x=x*1664525+1013904223;
    }
    return B_OK;
}
int main(int argc,char** argv)
{
    if(argc!=3) return 2;
    int priority=atoi(argv[1]), count=atoi(argv[2]);
    if((priority!=5 && priority!=10 && priority!=15 && priority!=20)
        || (count!=0 && count!=2)) return 2;
    if(!Pin() || set_thread_priority(find_thread(NULL),priority)<B_OK) return 3;
    Load load; thread_id ids[2]; int started=0,errors=0;
    for(int i=0;i<count;++i){
        thread_id id=spawn_thread(Worker,"lab latency estimator",B_NORMAL_PRIORITY,&load);
        if(id<0){++errors;break;}
        if(resume_thread(id)!=B_OK){kill_thread(id);wait_for_thread(id,NULL);++errors;break;}
        ids[started++]=id;
    }
    for(int i=0;i<200 && load.ready.load()<count;++i) snooze(1000);
    if(load.ready.load()!=count) ++errors;
    for(int i=0;i<20 && !errors;++i){
        bigtime_t estimate=estimate_max_scheduling_latency();
        printf("%d,%d,%d,%lld\n",priority,count,i+1,(long long)estimate);
        if(estimate<0 || _kern_get_cpu()!=0){++errors;break;}
        snooze(5000);
    }
    load.stop.store(true);
    for(int i=0;i<started;++i){
        status_t result=B_ERROR;
        if(wait_for_thread_etc(ids[i],B_RELATIVE_TIMEOUT,4000000,&result)!=B_OK){
            kill_thread(ids[i]);wait_for_thread(ids[i],NULL);++errors;
        } else if(result!=B_OK) ++errors;
    }
    return errors?1:0;
}
