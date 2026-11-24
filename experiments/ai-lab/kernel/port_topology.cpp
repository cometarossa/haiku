// AI-assisted independent Haiku research fork. MIT.
// Compare equal aggregate queue capacity and equal thread counts.
#include <OS.h>
#include <cstdio>
#include <cstdlib>
#include <cstring>

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
};

static status_t Run(void* data)
{
    Task& t = *static_cast<Task*>(data);
    for (int i = 0; i < kMessages; ++i) {
        if (t.writer) {
            Message m = {t.index, i};
            status_t s = write_port_etc(t.port, 42, &m, sizeof(m),
                B_RELATIVE_TIMEOUT, kTimeout);
            if (s != B_OK) return s;
        } else {
            int32 code = 0;
            ssize_t s = read_port_etc(t.port, &code, &t.received[i],
                sizeof(Message), B_RELATIVE_TIMEOUT, kTimeout);
            if (s != sizeof(Message) || code != 42) return B_ERROR;
            if (t.independent && t.received[i].producer != t.index)
                return B_ERROR;
        }
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
        if (id < 0) { ++errors; break; }
        threads[created++] = id;
    }
    bigtime_t start = system_time();
    int resumed = 0;
    if (!errors) {
        for (; resumed < created; ++resumed) {
            if (resume_thread(threads[resumed]) != B_OK) {
                ++errors; break;
            }
        }
    }
    for (int i = resumed; i < created; ++i)
        kill_thread(threads[i]);
    bool deleted = false;
    for (int i = 0; i < resumed; ++i) {
        status_t result = B_ERROR;
        status_t wait = wait_for_thread_etc(threads[i],
            B_RELATIVE_TIMEOUT, kTimeout, &result);
        if (wait == B_OK && result == B_OK) ++joined;
        else {
            ++errors;
            if (!deleted) {
                for (int j = 0; j < ports; ++j) delete_port(ids[j]);
                deleted = true;
            }
            if (wait != B_OK) {
                kill_thread(threads[i]); wait_for_thread(threads[i], NULL);
            }
        }
    }
    bigtime_t elapsed = system_time() - start;
    if (!deleted)
        for (int i = 0; i < ports; ++i)
            if (delete_port(ids[i]) != B_OK) ++errors;
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
    return errors ? 1 : 0;
}
