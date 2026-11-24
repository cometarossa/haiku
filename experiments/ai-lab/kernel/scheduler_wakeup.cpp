// AI-assisted independent Haiku research fork. MIT.
// Periodic absolute-deadline wakeup under bounded same-vCPU CPU load.
#include <OS.h>
#include <scheduler.h>
#include <atomic>
#include <cstdio>
#include <cstdlib>
#include <vector>
extern "C" int _kern_get_cpu();
extern "C" status_t _kern_set_thread_affinity(thread_id,const void*,size_t);
static const int kSamples=120;
static const bigtime_t kPeriod=5000;
struct Load {
    std::atomic<bool> stop{false};
    std::atomic<int> ready{0};
};
static bool Pin()
{
    uint32 mask[32]={1};
    if (_kern_set_thread_affinity(0,mask,sizeof(mask))!=B_OK) return false;
    for(int i=0;i<100 && _kern_get_cpu()!=0;++i) snooze(1000);
    return _kern_get_cpu()==0;
}
static status_t Busy(void* data)
{
    Load& load=*static_cast<Load*>(data);
    if(!Pin()) { load.ready.fetch_add(100); return B_ERROR; }
    load.ready.fetch_add(1);
    volatile uint64 work=1;
    while(!load.stop.load())
        for(int i=0;i<1024;++i) work=work*1664525+1013904223;
    return B_OK;
}
int main(int argc,char** argv)
{
    if(argc!=3) return 2;
    int priority=atoi(argv[1]), count=atoi(argv[2]);
    if((priority!=B_NORMAL_PRIORITY && priority!=B_DISPLAY_PRIORITY)
        || (count!=0 && count!=2)) return 2;
    if(!Pin()) return 3;
    if(set_thread_priority(find_thread(NULL),priority)<B_OK) return 4;
    thread_info info;
    if(get_thread_info(find_thread(NULL),&info)!=B_OK || info.priority!=priority) return 5;
    Load load;
    thread_id ids[2];
    int started=0,errors=0;
    for(int i=0;i<count;++i){
        thread_id id=spawn_thread(Busy,"lab bounded CPU load",B_NORMAL_PRIORITY,&load);
        if(id<0){++errors;break;}
        if(resume_thread(id)!=B_OK){kill_thread(id);wait_for_thread(id,NULL);++errors;break;}
        ids[started++]=id;
    }
    for(int i=0;i<200 && load.ready.load()<count;++i) snooze(1000);
    if(load.ready.load()!=count) ++errors;
    std::vector<bigtime_t> samples;
    samples.reserve(kSamples);
    bigtime_t due=system_time()+20000;
    for(int i=0;i<kSamples && !errors;++i){
        if(snooze_until(due,B_SYSTEM_TIMEBASE)!=B_OK || _kern_get_cpu()!=0){++errors;break;}
        bigtime_t now=system_time();
        if(now<due){++errors;break;}
        samples.push_back(now-due);
        due+=kPeriod;
    }
    load.stop.store(true);
    for(int i=0;i<started;++i){
        status_t status=B_ERROR;
        if(wait_for_thread_etc(ids[i],B_RELATIVE_TIMEOUT,2000000,&status)!=B_OK){
            kill_thread(ids[i]);wait_for_thread(ids[i],NULL);++errors;
        }else if(status!=B_OK) ++errors;
    }
    if(errors || samples.size()!=kSamples) return 6;
    for(int i=0;i<kSamples;++i)
        printf("%d,%d,%d,%d,%lld\n",get_scheduler_mode(),priority,count,i+1,(long long)samples[i]);
    return 0;
}
