/*
 * AI-assisted experimental Haiku Media Kit decoder probe, MIT License.
 * For cometarossa/haiku ai-experimental only; not for Haiku upstream.
 * Validates decoded frames and a stable pixel-byte digest, not FPS.
 */
#include <Entry.h>
#include <MediaFile.h>
#include <MediaTrack.h>
#include <MediaDefs.h>
#include <GraphicsDefs.h>
#include <SupportDefs.h>

#include <stdio.h>
#include <stdlib.h>
#include <stdint.h>
#include <string.h>


static uint64_t
hashPixels(uint64_t hash, const uint8_t* pixels, size_t bytes)
{
    for (size_t i = 0; i < bytes; ++i) {
        hash ^= pixels[i];
        hash *= UINT64_C(1099511628211);
    }
    return hash;
}

int
main(int argc, char** argv)
{
    if (argc != 2) {
        fprintf(stderr, "Usage: %s <H264-MP4-fixture>\n", argv[0]);
        return 2;
    }

    entry_ref reference;
    status_t status = get_ref_for_path(argv[1], &reference);
    if (status != B_OK) {
        fprintf(stderr, "get_ref_for_path failed: %ld\n", (long)status);
        return 2;
    }

    BMediaFile file(&reference);
    status = file.InitCheck();
    if (status != B_OK) {
        fprintf(stderr, "BMediaFile::InitCheck failed: %ld\n", (long)status);
        return 1;
    }

    BMediaTrack* track = NULL;
    media_format encoded;
    for (int32 i = 0; i < file.CountTracks(); ++i) {
        BMediaTrack* candidate = file.TrackAt(i);
        if (candidate == NULL)
            continue;
        status = candidate->EncodedFormat(&encoded);
        if (status == B_OK && encoded.IsVideo()) {
            track = candidate;
            break;
        }
        file.ReleaseTrack(candidate);
    }
    if (track == NULL) {
        fprintf(stderr, "No supported video track found\n");
        return 1;
    }

    uint32_t width = encoded.u.encoded_video.output.display.line_width;
    uint32_t height = encoded.u.encoded_video.output.display.line_count;
    if (width == 0 || height == 0 || width > 8192 || height > 8192) {
        fprintf(stderr, "Invalid video dimensions %lu x %lu\n",
            (unsigned long)width, (unsigned long)height);
        return 1;
    }

    media_format decoded;
    decoded.Clear();
    decoded.type = B_MEDIA_RAW_VIDEO;
    decoded.u.raw_video.display.format = B_RGB32;
    decoded.u.raw_video.display.line_width = width;
    decoded.u.raw_video.display.line_count = height;
    decoded.u.raw_video.display.bytes_per_row = width * 4;
    status = track->DecodedFormat(&decoded);
    if (status != B_OK) {
        fprintf(stderr, "BMediaTrack::DecodedFormat failed: %ld\n", (long)status);
        return 1;
    }

    const media_video_display_info& display = decoded.u.raw_video.display;
    if (display.format != B_RGB32 || display.line_width != width
        || display.line_count != height || display.bytes_per_row < width * 4) {
        fprintf(stderr, "Codec returned unexpected raw pixel format or geometry\n");
        return 1;
    }
    const uint64_t size = uint64_t(display.bytes_per_row) * height;
    if (size == 0 || size > 512 * 1024 * 1024) {
        fprintf(stderr, "Refusing invalid video buffer size\n");
        return 1;
    }
    uint8_t* buffer = static_cast<uint8_t*>(malloc(size));
    if (buffer == NULL)
        return 1;

    uint64_t digest = UINT64_C(14695981039346656037);
    int32 frameCount = 0;
    int64 expectedFrames = track->CountFrames();
    if (expectedFrames < 1 || expectedFrames > 10000) {
        fprintf(stderr, "Unsupported frame count: %lld\n",
            (long long)expectedFrames);
        return 1;
    }
    for (int64 frameIndex = 0; frameIndex < expectedFrames; ++frameIndex) {
        memset(buffer, 0, size);
        int64 oneFrame = 1;
        media_header header;
        memset(&header, 0, sizeof(header));
        status = track->ReadFrames(buffer, &oneFrame, &header);
        if (status != B_OK && status != B_LAST_BUFFER_ERROR) {
            fprintf(stderr, "ReadFrames failed at %ld: %ld\n",
                (long)frameCount, (long)status);
            return 1;
        }
        if (oneFrame != 1) {
            fprintf(stderr, "ReadFrames returned no frame at index %ld\n",
                (long)frameCount);
            return 1;
        }
        uint64_t frameDigest = UINT64_C(14695981039346656037);
        for (uint32_t row = 0; row < height; ++row) {
            const uint8_t* pixels = buffer
                + uint64_t(row) * display.bytes_per_row;
            digest = hashPixels(digest, pixels, size_t(width) * 4);
            frameDigest = hashPixels(frameDigest, pixels, size_t(width) * 4);
        }
        printf("FRAME %lld %lld %016llx\n", (long long)frameIndex,
            (long long)header.start_time, (unsigned long long)frameDigest);
        ++frameCount;
    }
    free(buffer);
    file.ReleaseTrack(track);
    printf("frames,width,height,format,hash_fnv1a64\n");
    printf("%ld,%lu,%lu,B_RGB32,%016llx\n", (long)frameCount,
        (unsigned long)width, (unsigned long)height,
        (unsigned long long)digest);
    fprintf(stderr, "Decoded frames=%ld, expected=%lld, hash=%016llx\n",
        (long)frameCount, (long long)expectedFrames,
        (unsigned long long)digest);
    return 0;
}
