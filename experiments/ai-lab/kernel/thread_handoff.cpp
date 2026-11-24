// AI-assisted independent Haiku research fork. MIT.
// Round-trip latency, not a direct measurement of context-switch time.
#include <OS.h>
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

static status_t Peer(void* arg)
{
    Channel& c = *static_cast<Channel*>(arg);
    for (int i = 0; i < kRounds + kWarmup; ++i) {
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
    if (argc != 2 || (strcmp(argv[1],"sem") && strcmp(argv[1],"port"))) return 2;
    bool sem = !strcmp(argv[1],"sem");
    Channel c = {sem, sem ? create_sem(0,"lab request") : create_port(1,"lab request"),
        sem ? create_sem(0,"lab reply") : create_port(1,"lab reply")};
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
        printf("%s,%d,%lld\n",argv[1],i+1,(long long)samples[i]);
    return 0;
}
