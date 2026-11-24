// AI-assisted independent research fork. MIT.
// Competing higher-priority reader drains a capacity-one port after waking
// a lower-priority waiter. Compare relative and absolute deadlines.
#include <OS.h>
#include <cstdio>
#include <cstring>
#include <atomic>
#include <initializer_list>
extern "C" int _kern_get_cpu();
extern "C" status_t _kern_set_thread_affinity(thread_id, const void*, size_t);
static const bigtime_t kBudget=150000;
struct Trial {
    port_id port;
    bool absolute, info;
    std::atomic<bool> done{false};
    bigtime_t elapsed=0;
    ssize_t result=B_ERROR;
};
static bool Pin()
{
    uint32 mask[32]={1};
    if (_kern_set_thread_affinity(0,mask,sizeof(mask))!=B_OK) return false;
    for(int i=0;i<100 && _kern_get_cpu()!=0;++i) snooze(1000);
    return _kern_get_cpu()==0;
}
static status_t Reader(void* data)
{
    Trial& t=*static_cast<Trial*>(data);
    if (!Pin()) { t.done.store(true); return B_ERROR; }
    int32 code;
    bigtime_t start=system_time();
    uint32 flags=t.absolute?B_ABSOLUTE_TIMEOUT:B_RELATIVE_TIMEOUT;
    bigtime_t deadline=t.absolute?start+kBudget:kBudget;
    t.result=t.info?port_buffer_size_etc(t.port,flags,deadline):
        read_port_etc(t.port,&code,NULL,0,flags,deadline);
    t.elapsed=system_time()-start;
    t.done.store(true);
    return B_OK;
}
static int Test(bool absolute,bool info,int repeat)
{
    Trial t; t.absolute=absolute; t.info=info;
    t.port=create_port(1,"deadline test");
    if(t.port<0) return 1;
    thread_id th=spawn_thread(Reader,"deadline waiter",B_LOW_PRIORITY,&t);
    if(th<0){delete_port(t.port);return 1;}
    if(resume_thread(th)!=B_OK){kill_thread(th);wait_for_thread(th,NULL);delete_port(t.port);return 1;}
    int drained=0, errors=0;
    for(int i=0;i<10 && !t.done.load();++i){
        snooze(30000);
        if(t.done.load()) break;
        thread_info ti;
        if(get_thread_info(th,&ti)!=B_OK || ti.state!=B_THREAD_WAITING){++errors;break;}
        if(write_port_etc(t.port,42,NULL,0,B_RELATIVE_TIMEOUT,0)!=B_OK){++errors;break;}
        int32 code=-1;
        if(read_port_etc(t.port,&code,NULL,0,B_RELATIVE_TIMEOUT,0)!=0 || code!=42){++errors;break;}
        ++drained;
    }
    status_t result=B_ERROR;
    status_t wait=wait_for_thread_etc(th,B_RELATIVE_TIMEOUT,1000000,&result);
    if(wait!=B_OK){delete_port(t.port);kill_thread(th);wait_for_thread(th,NULL);return 1;}
    delete_port(t.port);
    if(result!=B_OK || t.result!=B_TIMED_OUT || drained<2) ++errors;
    printf("%s,%s,%d,%d,%lld,%lld,%d\n",info?"info":"read",absolute?"absolute":"relative",repeat,drained,(long long)t.result,(long long)t.elapsed,errors);
    return errors?1:0;
}
int main()
{
    if(!Pin()) return 2;
    printf("api,timeout,repeat,drained,result,elapsed_us,errors\n");
    int errors=0;
    for(bool info:{false,true}) for(int i=1;i<=3;++i){
        errors+=Test(false,info,i);
        errors+=Test(true,info,i);
    }
    return errors?1:0;
}
