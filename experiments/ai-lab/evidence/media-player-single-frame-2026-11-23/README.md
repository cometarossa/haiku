# MediaPlayer one-frame cache isolation bug, reproduced and fixed

23 November 2026. AI-assisted, independent cometarossa/haiku fork,
branch ai-experimental. **Not submitted to upstream Haiku.**

## Reproducer

The official, unmodified source file
src/apps/mediaplayer/supplier/MediaTrackVideoSupplier.cpp used a
function-local static flag named already in ReadFrame(), for one-frame
videos (embedded cover art). That flag is shared by all instances of
MediaTrackVideoSupplier rather than by each media track.

Test: experiments/ai-lab/media/media_player_single_frame_regression.cpp.
The test creates two independent BMediaFile instances of the same
one-frame H.264 MP4 fixture, then calls ReadFrame on two independently
constructed MediaTrackVideoSupplier instances in sequence.

Fixture: one-frame MP4 made from the previously tested 150-frame
H.264 MP4 by the native guest's FFmpeg, using -frames:v 1 -c:v copy.
Both tracks explicitly reported CountFrames()=1.

Compilation: inside Haiku R1/beta6 on the throwaway QEMU overlay, native
GCC using actual MediaPlayer sources and native Media Kit libraries:

    g++ -std=c++11 -O2 -Wall -Wextra -I. \
      -o single_frame_regression test_single.cpp \
      MediaTrackVideoSupplier.cpp VideoTrackSupplier.cpp \
      ColorSpaceToString.cpp -lmedia -lbe

## Before patch — unmodified MediaPlayer source

- first,status=0,was_cached=0,wrote_pixels=1
- second,status=0,was_cached=1,wrote_pixels=0
- SINGLE_FRAME_INDEPENDENT_SUPPLIERS_FAIL; guest process exit 1.

The second independent video did not decode its first frame.

## Patch — isolated to research fork

Changed the shared static flag to bool fSingleFrameAlreadyRead,
initialized false in every MediaTrackVideoSupplier object.

The corrected source was transferred into the same unchanged Haiku
beta6 guest, recompiled with the identical test and fixture:

- first,status=0,was_cached=0,wrote_pixels=1
- second,status=0,was_cached=0,wrote_pixels=1
- SINGLE_FRAME_INDEPENDENT_SUPPLIERS_PASS; guest process exit 0.

Artifacts: guest-original stdout/stderr and QEMU screenshots before and
after the patch. SHA256SUMS records all original artifacts.

## Important limitations

The fix was verified by compiling the patched MediaPlayer supplier
sources and a native regression program within the reference beta6
guest. The beta6 MediaPlayer application binary and OS remain
unmodified; this was **not yet a full fork OS build or package install**.

An AI-assisted fork patch must never be submitted to the official Haiku
project due to the upstream project's contribution policy.

## Extended verification: two different covers and cache reuse

A stronger regression program was compiled and executed natively in the
same unmodified beta6 guest with the revised research-fork supplier.
The first one-frame video is H.264 and the second is a one-frame
MPEG-4 clip generated from another timestamp of the same controlled
test source using the guest FFmpeg encoder.

Two passes for each independent supplier were tested:
- Same file, two independent suppliers: both first reads returned
  status=0, was_cached=0, wrote_pixels=1, same decoded digest.
- Different files, two independent suppliers: both first reads returned
  status=0, was_cached=0, wrote_pixels=1; hashes differed.
- On each supplier, the second read returned was_cached=1 and
  wrote_pixels=0, confirming correct per-instance cache reuse.
- Both test variants returned SINGLE_FRAME_INDEPENDENT_SUPPLIERS_PASS.

The corrected supplier now sets its cache flag only after a successful
decoder read; this avoids making a failed first read permanent cache
state. Error-retry semantics on decoder failure were inspected in
source but not simulated by this functional test.

Artifacts: single_extended_same.stdout/.stderr,
single_extended_distinct.stdout/.stderr and
ai-fork-extended-cover-art-passes.png.
