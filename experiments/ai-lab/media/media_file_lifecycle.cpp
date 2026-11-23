/*
 * AI-assisted Haiku fork experiment. MIT License.
 * This file is not intended or permitted for upstream Haiku submission.
 *
 * Exercise Media Kit file and track resource lifetimes (correctness only).
 * No video is presented; this is NOT a playback FPS benchmark.
 */
#include <Entry.h>
#include <MediaFile.h>
#include <MediaTrack.h>
#include <OS.h>

#include <errno.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

static bool
parseIterations(const char* text, int* count)
{
    if (text == NULL || *text == '\0')
        return false;
    errno = 0;
    char* end = NULL;
    long parsed = strtol(text, &end, 10);
    if (errno != 0 || end == text || *end != '\0'
        || parsed < 1 || parsed > 100000)
        return false;
    *count = (int)parsed;
    return true;
}

int
main(int argc, char** argv)
{
    if (argc != 3) {
        fprintf(stderr, "Usage: %s <media-file> <iterations:1..100000>\n", argv[0]);
        return 2;
    }
    int iterations = 0;
    if (!parseIterations(argv[2], &iterations)) {
        fprintf(stderr, "Invalid iteration count: %s\n", argv[2]);
        return 2;
    }

    entry_ref reference;
    status_t entryStatus = get_ref_for_path(argv[1], &reference);
    if (entryStatus != B_OK) {
        fprintf(stderr, "Cannot locate media file %s: status=%ld\n",
            argv[1], (long)entryStatus);
        return 2;
    }

    int failures = 0;
    int firstTrackCount = -1;
    printf("iteration,init_status,tracks,first_track_status,elapsed_us\n");
    for (int i = 0; i < iterations; ++i) {
        const bigtime_t start = system_time();
        status_t initStatus = B_ERROR;
        status_t trackStatus = B_ERROR;
        int32 trackCount = -1;

        {
            BMediaFile media(&reference);
            initStatus = media.InitCheck();
            if (initStatus == B_OK) {
                trackCount = media.CountTracks();
                if (trackCount > 0) {
                    BMediaTrack* track = media.TrackAt(0);
                    if (track != NULL) {
                        trackStatus = track->InitCheck();
                        media.ReleaseTrack(track);
                    }
                } else {
                    trackStatus = B_OK;
                }
            }
        }

        const bigtime_t elapsed = system_time() - start;
        printf("%d,%ld,%ld,%ld,%lld\n", i + 1, (long)initStatus,
            (long)trackCount, (long)trackStatus, (long long)elapsed);
        fflush(stdout);

        if (initStatus != B_OK || trackCount < 1
            || trackStatus != B_OK)
            ++failures;
        if (firstTrackCount < 0)
            firstTrackCount = trackCount;
        else if (trackCount != firstTrackCount)
            ++failures;
    }
    fprintf(stderr, "Media Kit lifecycle: iterations=%d failures=%d\n",
        iterations, failures);
    return failures == 0 ? 0 : 1;
}
