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

**Validation status (2026-11-23):** Source prepared, not yet built or
executed in the guest. When the disposable boot image is available,
compile, run and inspect generated CSV on both the reference build and
the experimental build. Save original logs and the input file SHA256.
