// AI-assisted independent Haiku research fork. MIT.
// Bounded native kernel API correctness probe; not a bare-metal benchmark.
#include <OS.h>
#include <cstdio>
#include <cstdint>
#include <cstdlib>
#include <cstring>
#include <vector>

static const int kIterations = 1000;
static const int kMaxThreads = 8;
static const bigtime_t kTimeout = 5000000;
struct Message { int32 worker; int32 sequence; uint64 value; };
struct Context { port_id port; area_id area; int32 worker; };

static uint64 Value(int32 worker, int32 sequence)
{
    return (uint64(worker + 1) << 32) | uint32(sequence + 1);
}

static status_t Worker(void* arg)
{
    Context* c = static_cast<Context*>(arg);
    void* address = NULL;
    area_id clone = clone_area("lab worker clone", &address, B_ANY_ADDRESS,
        B_READ_AREA | B_WRITE_AREA, c->area);
    if (clone < 0)
        return clone;
    uint64* words = static_cast<uint64*>(address);
    status_t result = B_OK;
    for (int32 i = 0; i < kIterations; ++i) {
        Message m = {c->worker, i, Value(c->worker, i)};
        words[c->worker * kIterations + i] = m.value;
        result = write_port_etc(c->port, 42, &m, sizeof(m),
            B_RELATIVE_TIMEOUT, kTimeout);
        if (result != B_OK)
            break;
    }
    status_t cleanup = delete_area(clone);
    return result == B_OK ? cleanup : result;
}

int main(int argc, char** argv)
{
    int n = argc >= 2 ? atoi(argv[1]) : 4;
    int capacity = argc >= 3 ? atoi(argv[2]) : 16;
    if (argc > 3 || n < 1 || n > kMaxThreads
        || capacity < 1 || capacity > 256)
        return 2;
    port_id port = create_port(capacity, "lab bounded queue");
    if (port < 0) return 3;
    void* address = NULL;
    size_t bytes = ((n * kIterations * sizeof(uint64) + B_PAGE_SIZE - 1)
        / B_PAGE_SIZE) * B_PAGE_SIZE;
    area_id area = create_area("lab shared area", &address, B_ANY_ADDRESS,
        bytes, B_NO_LOCK, B_READ_AREA | B_WRITE_AREA | B_CLONEABLE_AREA);
    if (area < 0) { delete_port(port); return 4; }
    memset(address, 0, bytes);
    int32 code = 0;
    Message m = {};
    ssize_t empty = read_port_etc(port, &code, &m, sizeof(m),
        B_RELATIVE_TIMEOUT, 20000);
    bool emptyOK = empty == B_TIMED_OUT;
    Context contexts[kMaxThreads];
    thread_id threads[kMaxThreads];
    int started = 0, errors = 0, received = 0, joined = 0;
    std::vector<int> next(n, 0);
    bigtime_t start = system_time();
    for (int i = 0; i < n; ++i) {
        contexts[i] = {port, area, i};
        thread_id t = spawn_thread(Worker, "lab IPC worker",
            B_NORMAL_PRIORITY, &contexts[i]);
        if (t < 0) { ++errors; break; }
        if (resume_thread(t) != B_OK) {
            kill_thread(t); wait_for_thread(t, NULL); ++errors; break;
        }
        threads[started++] = t;
    }
    while (received < started * kIterations) {
        ssize_t size = read_port_etc(port, &code, &m, sizeof(m),
            B_RELATIVE_TIMEOUT, kTimeout);
        if (size != sizeof(m)) { ++errors; break; }
        ++received;
        if (code != 42 || m.worker < 0 || m.worker >= started
            || m.sequence != next[m.worker]
            || m.value != Value(m.worker, m.sequence)) { ++errors; break; }
        ++next[m.worker];
    }
    // Deleting the port wakes blocked writers on any failure.
    if (errors) delete_port(port);
    for (int i = 0; i < started; ++i) {
        status_t result = B_ERROR;
        status_t wait = wait_for_thread_etc(threads[i], B_RELATIVE_TIMEOUT,
            kTimeout, &result);
        if (wait == B_OK && result == B_OK) ++joined;
        else {
            ++errors;
            if (wait != B_OK) {
                kill_thread(threads[i]); wait_for_thread(threads[i], NULL);
            }
        }
    }
    bigtime_t elapsed = system_time() - start;
    uint64* words = static_cast<uint64*>(address);
    int verified = 0;
    for (int i = 0; i < n; ++i)
        for (int j = 0; j < kIterations; ++j)
            if (words[i * kIterations + j] == Value(i, j)) ++verified;
    if (!errors && delete_port(port) != B_OK) ++errors;
    if (delete_area(area) != B_OK) ++errors;
    if (!emptyOK || started != n || joined != n
        || received != n*kIterations || verified != n*kIterations) ++errors;
    printf("threads,expected,received,shared_verified,joined,empty_timeout_ok,errors,elapsed_us\n");
    printf("%d,%d,%d,%d,%d,%d,%d,%lld\n", n, n*kIterations,
        received, verified, joined, int(emptyOK), errors, (long long)elapsed);
    return errors ? 1 : 0;
}
