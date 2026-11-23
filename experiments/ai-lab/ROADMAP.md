# Fork development milestones — November 2026

All scripts and documents here are AI-assisted, belong to the
cometarossa/haiku ai-experimental branch, and must not be
submitted to the upstream official Haiku project.

## M0 — Reproducible baseline

- [x] Fork, separate AI-assisted branch, explicit non-submission policy.
- [x] Case-sensitive Mac checkout and independent buildtools clone.
- [x] Compile Haiku Jam on Mac; preserve persistent beta6 VM disk.
- [x] Local GNU awk and Python 3.12 available; fix Apple Clang version parsing.
- [x] Isolated Ubuntu 24.04 builder on local ZimaBlade: GCC 13, Python 3.12,
      NASM and native Linux Jam verified, with CPU/memory constrained.
- [x] Haiku Linux host-only configuration succeeds inside isolated builder.
- [ ] Complete x86_64 cross toolchain (Mac Clang currently blocked by missing
      libsupc++.a; prefer isolated Linux builder).
- [ ] Build baseline x86_64 image, separately from beta6.
- [ ] Boot disposable QEMU image; collect serial/GUI logs and functional tests.

## M1 — Media Kit correctness

- [x] Establish Haiku beta6 guest baseline: native BMediaFile/track
      lifecycle probe, 100/100 and 1000/1000 valid runs (CSV, stderr,
      screenshot, SHA256 manifest); **no bug identified yet**.
- [x] Concurrent Media Kit baseline: 4 threads x 100 and 8 threads x 100,
      all 1200 cycles valid; guest CSV, stderr and screenshot recorded.
- [ ] Identify a reproducible media_server or Media Kit defect.
- [ ] Add a controlled failing test (node lifecycle, malformed input or leaks).
- [ ] Confirm behavior on reference and experimental builds.
- [ ] Implement minimal fix exclusively in this fork, with regression tests.
- [ ] Publish machine-readable evidence and AI provenance.

## M2 — Desktop and SMP correctness

- [ ] Test app_server input/events and window lifecycle under stress.
- [ ] Test virtual-SMP correctness without claiming native speed.
- [ ] Keep driver/GPU performance tests on physical hardware.

## Native testing

Bare-metal benchmarking requires a dedicated native installation, identical
hardware, repeatable stimuli, real hardware frame/latency/power measurements.
