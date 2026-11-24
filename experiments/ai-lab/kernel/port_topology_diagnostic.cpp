// AI-assisted independent Haiku research fork. MIT.
// Diagnostic variant: record exact IPC, join and worker return status.
#include <OS.h>
#include <cstdio>
#include <cstdlib>
#include <cstring>
#include <unistd.h>

static const int kPairs = 4;
static const int kMessages = 500;
static const bigtime_t kTimeout = 5000000;
struct Message { int32 producer; int32 seq; };
struct Task {
    port_id port;
    int index;
    bool independent;
    bool writer;
    Message received[kMessages];
    int completed;
    ssize_t lastStatus;
    int32 lastCode;
};

static status_t Run(void* data)
{
    Task& t = *static_cast<Task*>(data);
    for (int i = 0; i < kMessages; ++i) {
        if (t.writer) {
            Message m = {t.index, i};
            status_t s = write_port_etc(t.port, 42, &m, sizeof(m),
                B_RELATIVE_TIMEOUT, kTimeout);
            t.lastStatus = s;
            if (s != B_OK) return s;
        } else {
            int32 code = 0;
            ssize_t s = read_port_etc(t.port, &code, &t.received[i],
                sizeof(Message), B_RELATIVE_TIMEOUT, kTimeout);
            t.lastStatus = s;
            t.lastCode = code;
            if (s < 0) return (status_t)s;
            if (s != sizeof(Message) || code != 42) return B_ERROR;
            if (t.independent && t.received[i].producer != t.index)
                return B_ERROR;
        }
        ++t.completed;
    }
    return B_OK;
}

int main(int argc, char** argv)
{
    if (argc != 2 || (strcmp(argv[1], "shared") != 0
        && strcmp(argv[1], "independent") != 0)) return 2;
    bool independent = strcmp(argv[1], "independent") == 0;
    int ports = independent ? kPairs : 1;
    port_id ids[kPairs];
    for (int i = 0; i < ports; ++i) {
        ids[i] = create_port(independent ? 16 : 16*kPairs, "lab topology");
        if (ids[i] < 0) {
            for (int j = 0; j < i; ++j) delete_port(ids[j]);
            return 3;
        }
    }
    Task tasks[2*kPairs] = {};
    thread_id threads[2*kPairs];
    int created = 0, errors = 0, joined = 0;
    for (int i = 0; i < 2*kPairs; ++i) {
        Task& t = tasks[i];
        t.index = i % kPairs;
        t.port = ids[independent ? t.index : 0];
        t.writer = i >= kPairs;
        t.independent = independent;
        thread_id id = spawn_thread(Run, "lab topology worker",
            B_NORMAL_PRIORITY, &t);
        if (id < 0) { fprintf(stderr,"spawn worker=%d status=%ld\n",i,(long)id); ++errors; break; }
        threads[created++] = id;
    }
    bigtime_t start = system_time();
    int resumed = 0;
    if (!errors) {
        for (; resumed < created; ++resumed) {
            status_t resume = resume_thread(threads[resumed]);
            if (resume != B_OK) {
                fprintf(stderr,"resume worker=%d status=%ld\n",resumed,(long)resume);
                ++errors; break;
            }
        }
    }
    bool reaped = true;
    for (int i = resumed; i < created; ++i) {
        kill_thread(threads[i]);
        if (wait_for_thread(threads[i], NULL) != B_OK)
            reaped = false;
    }
    bool deleted = false;
    for (int i = 0; i < resumed; ++i) {
        status_t result = B_ERROR;
        status_t wait = wait_for_thread_etc(threads[i],
            B_RELATIVE_TIMEOUT, kTimeout, &result);
        fprintf(stderr,"join worker=%d tid=%ld wait=%ld result=%ld\n",
            i,(long)threads[i],(long)wait,(long)result);
        if (wait == B_OK && result == B_OK) ++joined;
        else {
            ++errors;
            if (!deleted) {
                for (int j = 0; j < ports; ++j) delete_port(ids[j]);
                deleted = true;
            }
            if (wait != B_OK) {
                kill_thread(threads[i]);
                if (wait_for_thread(threads[i], NULL) != B_OK)
                    reaped = false;
            }
        }
    }
    bigtime_t elapsed = system_time() - start;
    if (!deleted)
        for (int i = 0; i < ports; ++i)
            if (delete_port(ids[i]) != B_OK) ++errors;
    if (reaped) for (int i = 0; i < created; ++i)
        fprintf(stderr,"worker=%d role=%s port=%ld completed=%d last_status=%lld code=%ld\n",
            i,tasks[i].writer?"write":"read",(long)tasks[i].port,tasks[i].completed,
            (long long)tasks[i].lastStatus,(long)tasks[i].lastCode);
    bool seen[kPairs][kMessages] = {};
    int verified = 0;
    if (joined == 2*kPairs) {
        for (int i = 0; i < kPairs; ++i) {
            for (int j = 0; j < kMessages; ++j) {
                Message m = tasks[i].received[j];
                if (m.producer < 0 || m.producer >= kPairs
                    || m.seq < 0 || m.seq >= kMessages
                    || seen[m.producer][m.seq]) { ++errors; continue; }
                seen[m.producer][m.seq] = true;
                ++verified;
            }
        }
    }
    if (verified != kPairs*kMessages || joined != 2*kPairs) ++errors;
    printf("%s,%d,%d,%d,%d,%d,%lld\n", argv[1], kPairs, ports,
        verified, joined, errors, (long long)elapsed);
    if (!reaped) { fflush(NULL); _exit(1); }
    return errors ? 1 : 0;
}
