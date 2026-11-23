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
