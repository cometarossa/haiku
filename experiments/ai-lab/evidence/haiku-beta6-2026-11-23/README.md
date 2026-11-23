# Haiku R1/beta6 Media Kit lifecycle baseline — 23 November 2026

**AI-assisted research-fork evidence; not an official Haiku test submission.**

## Setup

- Guest: unmodified Haiku R1/beta6 x86_64 installed disk, launched as a
  throwaway QEMU QCOW2 overlay. Original persistent beta6 disk preserved.
- Host: macOS x86_64, QEMU/HVF with 4 Penryn virtual cores, 8 GiB guest RAM,
  standard VGA and user-mode networking.
- Tested within the Haiku guest using native g++ and the native Haiku
  Media Kit (-lmedia -lbe), **not** the host compiler or FFmpeg.
- Source: ../../media/media_file_lifecycle.cpp.
- Input: testsrc2-720p30-150frames-h264.mp4, SHA-256
  f08dafbf7bc1d3088a8408f4a9b5a18298d390150a643eb3f62338cd319026c7
  (1280x720, 30 fps, 150 frames, H.264).
- Compile command:
  g++ -std=c++11 -O2 -Wall -Wextra -o media_probe m.cpp -lmedia -lbe.
- Runs: ./media_probe t.mp4 100 and ./media_probe t.mp4 1000,
  each with CSV and stderr files exported directly from the guest.

## Observed result

- 100/100 successful iterations, zero recorded failures.
- 1000/1000 successful iterations, zero recorded failures.
- Every iteration returned B_OK (status 0), one track and valid first-track
  initialization status.
- No BMediaFile or track lifecycle errors were observed in these runs.
- CSVs comprise 101 and 1001 lines respectively (header plus iterations).
- haiku-beta6-media-kit-1000.png is the unmodified QEMU screendump of the
  guest terminal at the end of the thousand-cycle run.

## Limitations

This test opens and releases the file and first track; it does **not**
decode frames, render video, verify absence of memory leaks, test repeated
cold media_server restarts, or demonstrate native hardware performance.
No regression was found; this is a reproducible correctness baseline for
future fork changes. Times in CSV are virtualized guest timings, not
comparative performance evidence.

See SHA256SUMS for evidence artifact hashes.

## Additional multi-threaded baseline

The fork-only native C++ Media Kit probe media_file_concurrency.cpp
was built inside the same unmodified Haiku R1/beta6 guest:

    g++ -std=c++11 -O2 -Wall -Wextra -pthread \
      -o media_parallel p.cpp -lmedia -lbe

Runs with the same H.264 input file:
- 4 pthreads x 100 iterations = 400/400 valid outcomes, 0 failures.
- 8 pthreads x 100 iterations = 800/800 valid outcomes, 0 failures.
- For all 1200 iterations: InitCheck status 0, one track, first-track
  status 0. Results were transferred directly from guest and verified
  against their original stderr summaries.

Evidence: media_parallel_4x100.csv, media_parallel_4x100.stderr,
media_parallel_8x100.csv, media_parallel_8x100.stderr, and
haiku-beta6-media-kit-concurrent.png.

This checks simultaneous resource lifecycles, **not** video decoding,
thread scheduling fairness, leak freedom, presented FPS or native
hardware performance. No Media Kit defect has been reproduced.
