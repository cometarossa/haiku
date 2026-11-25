/* Independent Haiku lab: measure post-timeout lock acquisition. MIT license. */
#include <Application.h>
#include <Looper.h>
#include <OS.h>
#include <stdio.h>

static const int kIterations = 50000;

struct TimeoutState {
    BLooper* looper;
    status_t result;
};

static int32
TimeoutWorker(void* data)
{
    TimeoutState* state = static_cast<TimeoutState*>(data);
    state->result = state->looper->LockWithTimeout(10000);
    if (state->result == B_OK)
        state->looper->Unlock();
    return 0;
}

static bool
Measure(BLooper& looper, const char* label, int round)
{
    if (looper.IsLocked())
        return false;
    int32 before = looper.CountLockRequests();
    bigtime_t start = system_time();
    for (int i = 0; i < kIterations; i++) {
        if (looper.LockWithTimeout(100000) != B_OK)
            return false;
        looper.Unlock();
    }
    bigtime_t elapsed = system_time() - start;
    int32 after = looper.CountLockRequests();
    printf("LOCK %s %d %d %" B_PRId32 " %" B_PRId32 " %" B_PRId64 "\n",
        label, round, kIterations, before, after, elapsed);
    return before == after;
}

int
main()
{
    BApplication app("application/x-vnd.cometarossa-looper-lock-probe");
    if (app.InitCheck() != B_OK)
        return 2;
    BLooper clean("lab-clean");
    BLooper timed("lab-timed");
    if (!clean.IsLocked() || !timed.IsLocked())
        return 3;
    clean.Unlock();
    int32 initial = timed.CountLockRequests();
    TimeoutState state = {&timed, B_ERROR};
    thread_id worker = spawn_thread(TimeoutWorker, "lab-timeout",
        B_NORMAL_PRIORITY, &state);
    if (worker < 0)
        return 4;
    if (resume_thread(worker) != B_OK)
        return 4;
    status_t workerResult;
    if (wait_for_thread(worker, &workerResult) != B_OK || workerResult != 0
        || state.result != B_TIMED_OUT)
        return 5;
    int32 held = timed.CountLockRequests();
    timed.Unlock();
    printf("TIMEOUT %" B_PRId32 " %" B_PRId32 " %" B_PRId32 " %" B_PRId32 "\n",
        state.result, initial, held, timed.CountLockRequests());
    // Alternate order to limit warm-up/order effects. No running looper
    // threads, no system settings changes, and no MediaPlayer required.
    for (int round = 0; round < 6; round++) {
        if (round % 2 == 0) {
            if (!Measure(clean, "clean", round) || !Measure(timed, "timed", round))
                return 6;
        } else {
            if (!Measure(timed, "timed", round) || !Measure(clean, "clean", round))
                return 6;
        }
    }
    return 0;
}
