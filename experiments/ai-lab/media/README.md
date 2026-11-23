# Media Kit lifecycle probe (AI-assisted fork-only)

This is a small, standalone Haiku-native C++ Media Kit probe.
It is *not* code for upstream Haiku; see ../../AGENTS.md.

Run **inside Haiku**, after confirming a native C++ compiler exists:

    c++ -std=c++11 -O2 -Wall -Wextra -o media_file_lifecycle \
      media_file_lifecycle.cpp -lmedia -lbe
    ./media_file_lifecycle /boot/home/testsrc2-720p30-150frames-h264.mp4 100 \
      > lifecycle.csv 2> lifecycle.stderr

Use a known-good media file with at least one track. The probe opens
the file using BMediaFile, discovers tracks and opens/closes track 0,
then releases resources repeatedly. Any nonzero status or track-count
instability is recorded as a failing iteration; the whole process
returns 1 if any failure occurs.

No frame decoding, rendering or GPU acceleration is tested. The elapsed
microseconds include file opens and media plugin setup, but they are
**not valid for comparing OS speed in virtual machines**.

**Validation status (2026-11-23):** Built inside the unmodified Haiku
R1/beta6 guest booted from a throwaway QCOW2 overlay. Native g++ build
succeeded; 100 and 1000 lifecycle tests passed without errors.
Original CSVs, stderr, screenshot and SHA256 evidence are under
../evidence/haiku-beta6-2026-11-23/. A new experimental kernel/image
is not built yet, so no comparison with fork modifications is possible.

## Multi-threaded open/close test

The standalone media_file_concurrency.cpp probe runs independent
BMediaFile lifecycles from up to 16 POSIX threads at the same time.
It records every outcome in CSV, including per-thread InitCheck(),
track count, and first-track status. It does not render frames.

Haiku-native build/run:

    g++ -std=c++11 -O2 -Wall -Wextra -pthread -o media_parallel \
      media_file_concurrency.cpp -lmedia -lbe
    ./media_parallel /boot/home/testsrc2-720p30-150frames-h264.mp4 4 100 \
      > media_concurrency.csv 2> media_concurrency.stderr

This is a correctness and reproducibility probe; timings inside QEMU
are not valid evidence of bare-metal speed. A real race needs to be
reproduced on unmodified Haiku and the experimental fork before any
fix is proposed.

## Decoded-video correctness probe

The Haiku-only program media_video_decode.cpp requests 32-bit RGB
output from BMediaTrack and decodes the complete finite video fixture.
It computes FNV-1a 64-bit over active pixel bytes, excluding stride
padding, and records the number of frames. Run the same fixture twice:
the frame count, geometry and hash should be identical. Different
pixel outputs or decoder versions may legitimately yield different
hashes; this does not claim bitwise equivalence to FFmpeg output.
The test does not present frames to the desktop, so it is NOT a
video playback performance benchmark.

    g++ -std=c++11 -O2 -Wall -Wextra -o media_decode \
      media_video_decode.cpp -lmedia -lbe
    ./media_decode /boot/home/testsrc2-720p30-150frames-h264.mp4

## MediaPlayer single-frame supplier isolation regression

MediaPlayer's MediaTrackVideoSupplier historically cached one-frame
cover art with a function-local static flag, shared between every
supplier instance. The fork-only media_player_single_frame_regression.cpp
uses two independently opened one-frame MP4 tracks to test that both
suppliers decode their *first* frame before returning wasCached=true
on any later request.

Build the test with the actual MediaPlayer supplier implementation,
VideoTrackSupplier base class and ColorSpaceToString helper, linked
against native Haiku Media Kit; use an independently generated
single-frame MP4 fixture. The test should fail against the unmodified
supplier if the suspected bug exists, and pass with the isolated fix.

## Extended cover-art test (native guest)

The single-frame regression now supports an optional second file,
tests both the first decode and a subsequent same-instance cache hit,
and records a decoded pixel hash. When the second file is supplied,
the decoded hashes must differ.

On 23 November 2026 the AI-fork fix was tested with two cases:
- Two independent suppliers for the same one-frame H264 cover.
- Two independent suppliers for different one-frame covers:
  the first is H264 and the second is MPEG-4 from another timestamp
  of the same controlled source fixture.

In both cases, the first read of each supplier decoded pixels and
returned wasCached=false, and the second read of each supplier
returned wasCached=true without changing the caller-provided buffer.
The two distinct covers produced distinct pixel digests. A separate
test ensures the cache state is only marked valid after successful
decoding, not before an attempted read.


### Prepared GUI files for the first complete-fork acceptance test

On 24 November 2026 MacPorts FFmpeg was unusable because the
system-installed libdav1d.6.dylib was missing. Rather than alter that
global software installation, the fixtures were generated with the
already-installed FFmpeg 7.1.4-Jellyfin binary on the ZimaBlade, from
the original 150-frame H264 testsrc2 video. Both transfers ran over
temporary LAN-only HTTP listeners, which were stopped afterwards.

Verified result: cover_h264.mp4 and cover_mpeg4.mp4 contain **one**
1280x720 video frame each (H.264 and MPEG-4 respectively). The
regular test_video_h264.mp4 contains **150** frames. The three files
are staged on the Mac in its guest-files/regular-gui directory, not
embedded into the Git repository. Exact SHA256 hashes are recorded
in GUI-FIXTURE-SHA256SUMS. The independent full desktop Haiku
guest must ingest and test these fixtures to complete GUI acceptance.
