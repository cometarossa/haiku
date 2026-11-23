/*
 * AI-assisted experimental fork-only regression for MediaPlayer.
 * Two independently constructed MediaTrackVideoSupplier instances must
 * each decode their own single-frame video before reporting it cached.
 * MIT license. Not submitted to the official Haiku project.
 */
#include "MediaTrackVideoSupplier.h"

#include <Entry.h>
#include <MediaFile.h>
#include <MediaTrack.h>

#include <stdio.h>
#include <stdint.h>
#include <string.h>
#include <vector>

static bool
didWrite(const std::vector<unsigned char>& buffer)
{
    for (size_t i = 0; i < buffer.size(); ++i) {
        if (buffer[i] != 0xa5)
            return true;
    }
    return false;
}

static uint64_t
digestPixels(const std::vector<unsigned char>& buffer)
{
    uint64_t digest = UINT64_C(14695981039346656037);
    for (size_t i = 0; i < buffer.size(); ++i) {
        digest ^= buffer[i];
        digest *= UINT64_C(1099511628211);
    }
    return digest;
}

static int
testSupplier(MediaTrackVideoSupplier& supplier, const char* name,
    bool* wasCached, uint64_t* resultDigest)
{
    const media_raw_video_format& format = supplier.Format().u.raw_video;
    uint32 width = format.display.line_width;
    uint32 height = format.display.line_count;
    uint32 bytesPerRow = format.display.bytes_per_row;
    if (width == 0 || height == 0 || bytesPerRow == 0 ||
        width > 8192 || height > 8192 ||
        uint64(bytesPerRow) * height > 128 * 1024 * 1024) {
        fprintf(stderr, "%s: invalid decoder output geometry\n", name);
        return 2;
    }
    std::vector<unsigned char> buffer(bytesPerRow * height, 0xa5);
    bigtime_t time = 0;
    *wasCached = false;
    status_t status = supplier.ReadFrame(buffer.data(), &time, format,
        *wasCached);
    const bool changed = didWrite(buffer);
    *resultDigest = digestPixels(buffer);
    printf("%s,status=%ld,was_cached=%d,wrote_pixels=%d,hash=%016llx\n", name,
        (long)status, *wasCached ? 1 : 0, changed ? 1 : 0,
        (unsigned long long)*resultDigest);
    if (status != B_OK || *wasCached || !changed)
        return 1;

    // Re-reading cover art through the same supplier should use its cache.
    std::vector<unsigned char> secondBuffer(buffer.size(), 0xa5);
    bool cachedAgain = false;
    status = supplier.ReadFrame(secondBuffer.data(), &time, format, cachedAgain);
    bool wroteAgain = didWrite(secondBuffer);
    printf("%s_again,status=%ld,was_cached=%d,wrote_pixels=%d\n", name,
        (long)status, cachedAgain ? 1 : 0, wroteAgain ? 1 : 0);
    if (status != B_OK || !cachedAgain || wroteAgain)
        return 1;
    return 0;
}

int
main(int argc, char** argv)
{
    if (argc != 2 && argc != 3) {
        fprintf(stderr, "Usage: %s <one-frame-mp4-file> [different-one-frame-mp4]\n",
            argv[0]);
        return 2;
    }
    entry_ref firstRef, secondRef;
    if (get_ref_for_path(argv[1], &firstRef) != B_OK
        || get_ref_for_path(argc == 3 ? argv[2] : argv[1], &secondRef) != B_OK)
        return 2;

    BMediaFile firstFile(&firstRef);
    BMediaFile secondFile(&secondRef);
    if (firstFile.InitCheck() != B_OK || secondFile.InitCheck() != B_OK
        || firstFile.CountTracks() < 1 || secondFile.CountTracks() < 1)
        return 2;

    BMediaTrack* firstTrack = firstFile.TrackAt(0);
    BMediaTrack* secondTrack = secondFile.TrackAt(0);
    if (!firstTrack || !secondTrack)
        return 2;

    printf("track_frames=%lld,%lld\n",
        (long long)firstTrack->CountFrames(),
        (long long)secondTrack->CountFrames());
    if (firstTrack->CountFrames() != 1 || secondTrack->CountFrames() != 1) {
        fprintf(stderr, "Fixture is not a one-frame video\n");
        return 2;
    }

    status_t firstInit = B_ERROR;
    status_t secondInit = B_ERROR;
    MediaTrackVideoSupplier first(firstTrack, 0, firstInit);
    MediaTrackVideoSupplier second(secondTrack, 0, secondInit);
    if (firstInit != B_OK || secondInit != B_OK) {
        fprintf(stderr, "Failed to initialize video suppliers: %ld %ld\n",
            (long)firstInit, (long)secondInit);
        return 2;
    }

    bool firstCached = false;
    bool secondCached = false;
    uint64_t firstDigest = 0;
    uint64_t secondDigest = 0;
    int firstResult = testSupplier(first, "first", &firstCached, &firstDigest);
    int secondResult = testSupplier(second, "second", &secondCached, &secondDigest);
    if (argc == 3 && firstDigest == secondDigest) {
        fprintf(stderr, "Two distinct cover images produced identical pixels\n");
        secondResult = 1;
    }

    if (firstResult == 0 && secondResult == 0) {
        puts("SINGLE_FRAME_INDEPENDENT_SUPPLIERS_PASS");
        return 0;
    }
    puts("SINGLE_FRAME_INDEPENDENT_SUPPLIERS_FAIL");
    return 1;
}
