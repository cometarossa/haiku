// AI-assisted independent Haiku research fork. MIT.
// Bounded independent anonymous areas, first touch, aliases and lifetime.
#include <OS.h>
#include <atomic>
#include <cstdio>
#include <cstdlib>
extern "C" int _kern_get_cpu();
extern "C" status_t _kern_set_thread_affinity(thread_id,const void*,size_t);
struct Result {
    int worker, pages;
    std::atomic<int>* ready;
    std::atomic<bool>* start;
    std::atomic<bool>* abort;
    bigtime_t create, touch, clone, verify, destroy;
    int checked;
};
static uint64 Pattern(int worker,int page)
{
    return (uint64(worker+1)<<32)|uint32(page+1);
}
static status_t Work(void* arg)
{
    Result& r=*static_cast<Result*>(arg);
    uint32 mask[32]={uint32(1)<<r.worker};
    if(_kern_set_thread_affinity(0,mask,sizeof(mask))!=B_OK) return B_ERROR;
    r.ready->fetch_add(1);
    while(!r.start->load()){
        if(r.abort->load())return B_ERROR;
        snooze(1000);
    }
    if(r.abort->load())return B_ERROR;
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
int main(int argc,char** argv)
{
    if(argc!=3)return 2;
    int n=atoi(argv[1]),pages=atoi(argv[2]);
    if((n!=1&&n!=4)||(pages!=64&&pages!=256&&pages!=1024&&!(n==1&&pages==8192)))return 2;
    std::atomic<int> ready{0};
    std::atomic<bool> start{false},abort{false};
    Result results[4]={};
    thread_id ids[4];
    int started=0,errors=0;
    for(int i=0;i<n;++i){
        results[i]={i,pages,&ready,&start,&abort,0,0,0,0,0,0};
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
        printf("%d,%d,%d,%lld,%lld,%lld,%lld,%lld,%d\n",n,pages,i,
            (long long)r.create,(long long)r.touch,(long long)r.clone,
            (long long)r.verify,(long long)r.destroy,r.checked);
    }
    return 0;
}
