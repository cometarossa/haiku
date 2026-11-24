// AI-assisted independent Haiku research fork. MIT.
// Bounded empty-port deadline simulation of Media Kit wake-ahead timing.
// Real-time priority is used only by the sleeping observer.
#include <OS.h>
#include <scheduler.h>
#include <atomic>
#include <cstdio>
#include <cstdlib>
#include <cstring>
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
    if(argc!=4) return 2;
    int priority=atoi(argv[1]), count=atoi(argv[2]);
    bool compensate = strcmp(argv[3],"estimate")==0;
    if((priority!=10 && priority!=15 && priority!=100 && priority!=110)
        || (count!=0 && count!=2)
        || (!compensate && strcmp(argv[3],"none"))) return 2;
    if(!Pin() || set_thread_priority(find_thread(NULL),priority)<B_OK) return 3;
    thread_info info;
    if(get_thread_info(find_thread(NULL),&info)!=B_OK || info.priority!=priority) return 4;
    port_id port=create_port(1,"lab media timing");
    if(port<0) return 5;
    Load load; thread_id ids[2]; int started=0,errors=0;
    for(int i=0;i<count;++i){
        thread_id id=spawn_thread(Worker,"lab latency estimator",B_NORMAL_PRIORITY,&load);
        if(id<0){++errors;break;}
        if(resume_thread(id)!=B_OK){kill_thread(id);wait_for_thread(id,NULL);++errors;break;}
        ids[started++]=id;
    }
    for(int i=0;i<200 && load.ready.load()<count;++i) snooze(1000);
    if(load.ready.load()!=count) ++errors;
    constexpr int samples=80;
    constexpr bigtime_t period=10000;
    bigtime_t estimates[samples], signedError[samples];
    bigtime_t estimate=estimate_max_scheduling_latency();
    bigtime_t advance=compensate?estimate:0;
    int completed=0;
    if(estimate<0 || estimate>2500 || get_scheduler_mode()!=SCHEDULER_MODE_LOW_LATENCY)
        ++errors;
    bigtime_t due=system_time()+20000;
    for(int i=0;i<samples && !errors;++i){
        int32 code=0;
        bigtime_t waitUntil=due-advance;
        // A deadline already passed is a valid observation, not a failure.
        ssize_t status=read_port_etc(port,&code,NULL,0,B_ABSOLUTE_TIMEOUT,waitUntil);
        bigtime_t now=system_time();
        if(status!=B_TIMED_OUT || _kern_get_cpu()!=0){++errors;break;}
        estimates[i]=estimate;
        signedError[i]=now-due;
        ++completed;
        due+=period;
    }
    load.stop.store(true);
    for(int i=0;i<started;++i){
        status_t result=B_ERROR;
        if(wait_for_thread_etc(ids[i],B_RELATIVE_TIMEOUT,4000000,&result)!=B_OK){
            kill_thread(ids[i]);wait_for_thread(ids[i],NULL);++errors;
        } else if(result!=B_OK) ++errors;
    }
    if(delete_port(port)!=B_OK) ++errors;
    if(errors || completed!=samples) return 6;
    for(int i=0;i<samples;++i)
        printf("%d,%d,%s,%d,%lld,%lld,%lld\n",priority,count,argv[3],i+1,
            (long long)estimates[i],(long long)advance,(long long)signedError[i]);
    return 0;
}
