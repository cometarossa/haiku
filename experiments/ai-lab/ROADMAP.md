# Fork development milestones — November 2026

All scripts and documents here are AI-assisted, belong to the
cometarossa/haiku ai-experimental branch, and must not be
submitted to the upstream official Haiku project.

## Scope

Prioritize OS internals: kernel/SMP, memory, IPC, app_server, Media Kit,
media_server, drivers and architecture portability. Existing bundled
applications are regression probes only. Defer third-party application
ports and new application development (including Medo).

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
- [x] Boot the complete desktop (@nightly-raw), CI run 45285916285,
      revision d1e0b80c; verified desktop and guest fixture hashes.
- [x] Rebuild and boot V2, CI run 45290072750, revision d800dd54.
- [ ] Finish GUI acceptance: previous H.264 single-frame divide error
      not observed on V2, but video area remains black.

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
- [x] Baseline native kernel ports, shared-area clones, thread joins and
      timeouts: 1/4/8 producers, 13,000/13,000 messages verified.
- [x] Repeat identical kernel probe on V2: binary SHA256 verified,
      13,000/13,000 messages and shared values, zero errors.
- [x] Shared-port capacity sweep (16/64/256), 4/8 producers on both
      beta6 and V2: 72,000 messages and shared values verified.
- [x] Reproduce kernel IPC false-success on unreadable user buffer in
      both guests; fix shadowed copy status in port.cpp.
- [x] Rebuild and boot corrected V3 kernel, native copy-error test
      passes: B_BAD_ADDRESS, queue empty, valid write/read recovers.
- [x] Compare shared and independent ports, equal aggregate capacity,
      four producer/consumer pairs, three runs per mode per guest;
      24,000 messages verified, no errors.
- [x] Single-thread nonblocking IPC baseline, 0/64/4096-byte payloads,
      batch 1/64, three repeats: 147,456 messages verified.
- [x] Compare native semaphore and zero-payload port round-trip
      handoffs: 6,000 samples retained, median/P95/P99 computed.
- [x] Compare verified vCPU affinity handoffs on beta6 and V3,
      12,000 total samples, identical binary.
- [x] Competing-reader port deadline regression: 24 trials on beta6/V3;
      relative and absolute 150ms deadlines preserved in tested syscalls.
- [x] Periodic wakeup baseline at normal/display priority, idle and
      same-vCPU CPU load, 2880 samples on beta6/V3.
- [x] Compare low-latency/power-saving scheduler modes on V3, 2880
      samples, original mode restored.
- [x] CPU throughput/fairness baseline: four equal-priority workers on
      1/4 vCPUs, 12 runs on beta6/V3, 48 digests verified.
- [x] V4 regular desktop CI build 45348558239 succeeded; unified native
      regression suite implemented and smoke-tested on V3.
- [x] Boot V4 and pass unified regression suite, 90728 messages,
      480 wakeups, eight CPU worker digests.
- [x] Alternate V3/V4 six complete suites; loaded median P99 roughly
      halved, CPU throughput median loss within 5%; uncontrolled host.
- [x] Reproduce degenerate scheduling-latency estimate on beta6/V4
      (320 calls returning 100us); investigate and test a candidate fix.
- [x] V4 baseline for Media Kit-like empty-port deadline simulation,
      including sleeping real-time-priority observers: 1280 samples.
- [x] V5 compiled, restarted on migrated storage and native estimator
      test passed (160 calls, idle 500/1000us, loaded 1500us).
- [x] V5 initial Media Kit-like deadline simulation, 1280 samples;\n      signed error comparison archived (uncontrolled host).\n- [x] V5 native IPC/scheduler regression smoke suite: 90,728 messages,
      480 wakeup samples, eight verified CPU worker digests, no errors.
- [ ] Repeat V4/V5 timing under matched host conditions; extend VM tests.
- [x] Anonymous area lifecycle baseline beta6/V5, 42 bounded runs;
      zero-fill, clone coherence and survival after source deletion.
- [x] Same/split-vCPU first-touch vs warm-access comparison, beta6/V5;
      36 runs, 144 worker rows, strong placement-dependent slowdown.
- [x] Shared vs independent teams first-touch experiment, 72 runs;
      slowdown concentrated in shared address space across vCPUs.
- [ ] Trace first-touch mapping and synchronous TLB invalidation paths;
      isolate measured event counts before modifying kernel semantics.
- [ ] Complete controlled V4 evaluation (500us base,
      100us minimum, 2500us target; unchanged multipliers and power mode).
      Keep V3 as reference until latency, throughput and correctness pass.
- [ ] Isolate lock contention, wait/wakeup and allocator costs; repeat
      under controlled VM load and test cross-team IPC/scheduler fairness.
- [ ] Test virtual-SMP correctness without claiming native speed.
- [ ] Keep driver/GPU performance tests on physical hardware.

## Native testing

Bare-metal benchmarking requires a dedicated native installation, identical
hardware, repeatable stimuli, real hardware frame/latency/power measurements.
