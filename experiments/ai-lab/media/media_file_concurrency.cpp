/*
 * AI-assisted research fork experiment, MIT License.
 * Not submitted to the official Haiku project.
 *
 * Concurrent open/close and independent track lifetimes in Media Kit.
 * No video presentation or performance comparison is performed.
 */
#include <Entry.h>
#include <MediaFile.h>
#include <MediaTrack.h>
#include <OS.h>

#include <pthread.h>
#include <atomic>
#include <errno.h>
#include <stdio.h>
#include <stdlib.h>
#include <vector>

struct Outcome {
    int iteration;
    status_t init;
    int32 tracks;
    status_t firstTrack;
};

struct Worker {
    int threadID;
    int iterations;
    const entry_ref* file;
    Outcome* results;
    std::atomic<int>* start;
};

static void*
runWorker(void* argument)
{
    Worker* worker = static_cast<Worker*>(argument);
    while (worker->start->load(std::memory_order_acquire) == 0)
        snooze(1000);

    for (int i = 0; i < worker->iterations; ++i) {
        Outcome result = {i + 1, B_ERROR, -1, B_ERROR};
        {
            BMediaFile media(worker->file);
            result.init = media.InitCheck();
            if (result.init == B_OK) {
                result.tracks = media.CountTracks();
                if (result.tracks > 0) {
                    BMediaTrack* track = media.TrackAt(0);
                    if (track != NULL) {
                        result.firstTrack = track->InitCheck();
                        media.ReleaseTrack(track);
                    }
                }
            }
        }
        worker->results[i] = result;
    }
    return NULL;
}

static bool
positiveInt(const char* string, int maximum, int* result)
{
    if (!string || !*string)
        return false;
    errno = 0;
    char* end = NULL;
    long value = strtol(string, &end, 10);
    if (errno != 0 || end == string || *end != '\0' || value <= 0
        || value > maximum)
        return false;
    *result = static_cast<int>(value);
    return true;
}

int
main(int argc, char** argv)
{
    int threadCount, iterations;
    if (argc != 4
        || !positiveInt(argc > 2 ? argv[2] : NULL, 16, &threadCount)
        || !positiveInt(argc > 3 ? argv[3] : NULL, 10000, &iterations)) {
        fprintf(stderr, "Usage: %s <media-file> <threads:1..16> <iterations:1..10000>\n", argv[0]);
        return 2;
    }

    entry_ref reference;
    status_t status = get_ref_for_path(argv[1], &reference);
    if (status != B_OK) {
        fprintf(stderr, "Invalid path; status=%ld\n", (long)status);
        return 2;
    }

    std::vector<pthread_t> threads(threadCount);
    std::vector<Worker> workers(threadCount);
    std::vector<Outcome> results(threadCount * iterations);
    std::atomic<int> start(0);
    int created = 0;
    for (int i = 0; i < threadCount; ++i) {
        workers[i] = {i, iterations, &reference, &results[i * iterations], &start};
        int err = pthread_create(&threads[i], NULL, runWorker, &workers[i]);
        if (err != 0) {
            fprintf(stderr, "pthread_create failed at %d, errno=%d\n", i, err);
            break;
        }
        ++created;
    }
    start.store(1, std::memory_order_release);

    for (int i = 0; i < created; ++i)
        pthread_join(threads[i], NULL);
    if (created != threadCount)
        return 2;

    int failed = 0;
    printf("thread,iteration,init_status,tracks,first_track_status\n");
    for (int t = 0; t < threadCount; ++t) {
        for (int i = 0; i < iterations; ++i) {
            const Outcome& o = results[t * iterations + i];
            printf("%d,%d,%ld,%ld,%ld\n", t, o.iteration,
                (long)o.init, (long)o.tracks, (long)o.firstTrack);
            if (o.init != B_OK || o.tracks != 1 || o.firstTrack != B_OK)
                ++failed;
        }
    }
    fflush(stdout);
    fprintf(stderr, "Media Kit concurrent lifecycle: threads=%d iterations=%d"
        " cycles=%d failures=%d\n", threadCount, iterations,
        threadCount * iterations, failed);
    return failed == 0 ? 0 : 1;
}
