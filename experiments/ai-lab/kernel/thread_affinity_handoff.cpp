// AI-assisted independent Haiku research fork. MIT.
// Round-trip latency, not a direct measurement of context-switch time.
#include <OS.h>
#include <cstdint>

// Private Haiku syscall ABI, for this kernel laboratory only.
extern "C" int _kern_get_cpu();
extern "C" status_t _kern_get_thread_affinity(thread_id, void*, size_t);
extern "C" status_t _kern_set_thread_affinity(thread_id, const void*, size_t);
#include <cstdlib>
#include <algorithm>
#include <cstdio>
#include <cstring>
#include <vector>

static const int kRounds = 500;
static const int kWarmup = 20;
static const bigtime_t kTimeout = 2000000;
struct Channel {
    bool sem;
    int32 request, reply;
    int cpu;
};

static status_t Send(bool sem, int32 id, int32 seq)
{
    if (sem) return release_sem(id);
    return write_port_etc(id, seq, NULL, 0, B_RELATIVE_TIMEOUT, kTimeout);
}

static status_t Receive(bool sem, int32 id, int32 seq)
{
    if (sem) return acquire_sem_etc(id, 1, B_RELATIVE_TIMEOUT, kTimeout);
    int32 code = -1;
    ssize_t size = read_port_etc(id, &code, NULL, 0, B_RELATIVE_TIMEOUT, kTimeout);
    if (size < 0) return size;
    return size == 0 && code == seq ? B_OK : B_ERROR;
}

static bool Pin(int cpu)
{
    uint32_t mask[32] = {}, actual[32] = {};
    mask[cpu / 32] = uint32_t(1) << (cpu % 32);
    if (_kern_set_thread_affinity(0, mask, sizeof(mask)) != B_OK
        || _kern_get_thread_affinity(0, actual, sizeof(actual)) != B_OK
        || memcmp(mask, actual, sizeof(mask))) return false;
    for (int i=0; i<100 && _kern_get_cpu()!=cpu; ++i) snooze(1000);
    return _kern_get_cpu()==cpu;
}

static status_t Peer(void* arg)
{
    Channel& c = *static_cast<Channel*>(arg);
    if (!Pin(c.cpu)) return B_ERROR;
    for (int i = 0; i < kRounds + kWarmup; ++i) {
        if (_kern_get_cpu()!=c.cpu) return B_ERROR;
        status_t s = Receive(c.sem, c.request, i);
        if (s != B_OK) return s;
        s = Send(c.sem, c.reply, i);
        if (s != B_OK) return s;
    }
    return B_OK;
}

static void Destroy(Channel& c)
{
    for (int32 id : {c.request,c.reply}) {
        if (id < 0) continue;
        if (c.sem) delete_sem(id);
        else delete_port(id);
    }
}

int main(int argc, char** argv)
{
    if (argc != 3 || (strcmp(argv[1],"sem") && strcmp(argv[1],"port"))) return 2;
    if (strcmp(argv[2],"same") && strcmp(argv[2],"split")) return 2;
    int peerCPU = !strcmp(argv[2],"same") ? 0 : 1;
    if (!Pin(0)) return 7;
    bool sem = !strcmp(argv[1],"sem");
    Channel c = {sem, sem ? create_sem(0,"lab request") : create_port(1,"lab request"),
        sem ? create_sem(0,"lab reply") : create_port(1,"lab reply"), peerCPU};
    if (c.request < 0 || c.reply < 0) { Destroy(c); return 3; }
    thread_id peer = spawn_thread(Peer,"lab handoff peer", B_NORMAL_PRIORITY,&c);
    if (peer < 0) { Destroy(c); return 4; }
    if (resume_thread(peer) != B_OK) {
        kill_thread(peer); wait_for_thread(peer,NULL); Destroy(c); return 5;
    }
    std::vector<bigtime_t> samples;
    samples.reserve(kRounds);
    status_t s = B_OK;
    for (int i = 0; i < kRounds + kWarmup; ++i) {
        if (_kern_get_cpu()!=0) { s=B_ERROR; break; }
        bigtime_t start = system_time();
        s = Send(sem,c.request,i);
        if (s != B_OK) break;
        s = Receive(sem,c.reply,i);
        if (s != B_OK) break;
        if (i >= kWarmup) samples.push_back(system_time()-start);
    }
    status_t result = B_ERROR;
    status_t joined = wait_for_thread_etc(peer,B_RELATIVE_TIMEOUT,kTimeout,&result);
    if (joined != B_OK) { kill_thread(peer); wait_for_thread(peer,NULL); }
    Destroy(c);
    if (s != B_OK || joined != B_OK || result != B_OK || samples.size()!=kRounds)
        return 6;
    // Preserve every sample for independent percentile computation.
    for (int i = 0; i < kRounds; ++i)
        printf("%s,%s,%d,%lld\n",argv[1],argv[2],i+1,(long long)samples[i]);
    return 0;
}
