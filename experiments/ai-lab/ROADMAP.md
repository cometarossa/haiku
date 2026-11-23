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
- [x] Complete and verify cross toolchain on GitHub Actions
      run 45274740500: GCC 13.3.0 and GNU binutils 2.46.1 for
      x86_64-unknown-haiku. The separate Zima local GCC build is partial.
- [x] Build minimum x86_64 raw image in CI run 45282976284,
      with successful cross-toolchain, image and artifact SHA256 checks.
- [x] Boot fork-built minimum Haiku in QEMU/HVF and visually verify
      desktop, Tracker and Deskbar. Evidence in
      evidence/fork-minimum-boot-2026-11-24; only minimal OS profile.
- [ ] Boot the complete desktop (@nightly-raw) with patched MediaPlayer,
      then repeat native tests and validate missing optional libraries.

## M1 — Media Kit correctness

- [x] Establish Haiku beta6 guest baseline: native BMediaFile/track
      lifecycle probe, 100/100 and 1000/1000 valid runs (CSV, stderr,
      screenshot, SHA256 manifest); no file/track lifecycle failure.
- [x] Concurrent Media Kit baseline: 4 threads x 100 and 8 threads x 100,
      all 1200 cycles valid; guest CSV, stderr and screenshot recorded.
- [x] Native Haiku Media Kit H.264 decode: two complete runs of 150
      1280x720 B_RGB32 frames, identical pixel FNV-1a 64 digest.
### MediaPlayer single-frame decoding

- [x] Reproduce on unchanged beta6: second independent one-frame video
      returned was_cached=1 without decoding pixels.
- [x] Implement minimal fork-only state fix and recompile actual supplier
      source against the native Haiku Media Kit; verify exit 1 before,
      exit 0 after.
- [x] Test distinct H.264 and MPEG-4 one-frame covers; ensure each
      produces different pixels and subsequent per-instance cache hits.
- [x] Mark each cover-art cache valid only after successful decoding.
- [x] Preserve native logs, screenshots, SHA256 manifests and regression
      tests with AI provenance; 9/9 checks passing locally and on CI.
- [ ] Build complete patched MediaPlayer executable, integrate in a
      disposable Haiku OS image and test GUI playback/cover switching.
      The minimum-raw image does not ship MediaPlayer; the independent
      manual nightly-raw workflow builds the regular desktop with it.

### Media Kit and media_server remaining work

- [ ] Identify a separate reproducible media_server or Media Kit defect,
      such as a failed node lifecycle, malformed input or resource leak.
- [ ] Verify unchanged reference, add controlled test and implement an
      isolated fix on our own fork with regression evidence.

## M2 — Desktop and SMP correctness

- [x] Establish native beta6 app_server lifecycle baseline: 40 and 200
      GUI BWindow loops created and closed, 0 errors; exported CSV,
      stderr and screenshot. Fork-built image comparison still pending.
- [ ] Extend app_server event/input correctness tests and reproduce any
      real bugs under controlled conditions.
- [ ] Test virtual-SMP correctness without claiming native speed.
- [ ] Keep driver/GPU performance tests on physical hardware.

## Native testing

Bare-metal benchmarking requires a dedicated native installation, identical
hardware, repeatable stimuli, real hardware frame/latency/power measurements.
