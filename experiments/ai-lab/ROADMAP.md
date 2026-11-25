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
- [x] Inspect x86-64 Map: absent entries are installed without direct TLB invalidation.
- [ ] V6 diagnostic candidate: opt-in user map lock/flush counters via KDL;
      compile, boot, compare snapshot deltas and measure instrumentation overhead.
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

- [x] Phase-separated first-read/write baseline on beta6 and V5: 72 runs, 288 worker rows; first access isolated from create/delete and clone operations.

- [x] Demand-paged vs fully wired anonymous areas, beta6/V5, 72 runs; compare creation plus first access, retain bounded wiring as diagnostic control, not a default policy.

- [x] V6 boot and initial HVF/TCG lock/flush snapshots captured; preliminary evidence retained.
- [ ] V7a: distinguish outer map acquisition and hold durations; build, boot and validate paired windows before tuning.

- [x] V7a boot and 12 HVF paired diagnostic windows at 1024 pages; 9 benchmark runs, 36 workers, 73,728 alias checks; lock acquisition dominates observed hold/flush time in shared-team spread-vCPU cases.
- [ ] Complete remaining V7a acceptance: on/off, 256-page cases, TCG, regression; isolate mutex handoff before tuning.

- [ ] V7b x86_64 opt-in translation-map mutex queue and handoff-to-return diagnostics; compile/boot and compare paired windows before changing lock policy.

- [x] V7a smaller 256-page off-state HVF reference: 12 runs, 48 workers, 24,576 checks; no diagnostic sampling required to reproduce contention.

- [x] V7b regular CI 45444127880, image checksums and isolated boot; initial three paired HVF windows, 4096 page checks, no invalid mutex timestamp samples. Repeat before tuning.

- [x] V7b six additional 256-page paired HVF windows; combined three shared-team spread-vCPU and three independent-team windows, two same-vCPU controls. 12,288 additional alias checks, no invalid timestamps. Queue and resume costs both elevated; investigate dispatch/queue before tuning.

- [ ] V8 opt-in bounded x86_64 user translation-map trylock candidate; compare same-image off/on and V7b reference, verify correctness/fairness and CPU cost before any default enablement.

- [x] V8 boot and initial paired HVF off/on test: 48 runs, 192 worker rows; bounded trylock benefit measured; full regression and native gates remain pending.

- [ ] V8 regression interrupted: three suites passed; fourth (policy off) failed independent IPC topology; preserve evidence and isolate/reproduce before acceptance or purging reference images.

- [x] Isolated IPC topology reproduction V5/V7b/V8 off: 60 runs, 120,000 messages, no failures. Original suite failure remains open; replay preceding stages with detailed return codes.

- [x] IPC prefix replay on V5/V7b/V8 off: nine sequences, 54 stages, 153,000 verified messages; immediate uploads perturb timing; original intermittent failure remains open. Diagnostic per-worker source drafted; native build and validation pending.

- [x] Native offscreen app_server draw/sync baseline Beta6/V5/V8 off: 27 runs, 1,769,472 final RGB pixel checks. Diagnostic IPC variant compiled and passed 6 runs/12,000 messages; original intermittent failure open.

- [ ] V9 Interface Kit candidate: queue synchronous bitmap draw and AS_SYNC together where possible; retain reply and async behavior. Compile/boot, verify pixels and lifetime, measure packet counts and desktop regressions.

- [x] V9 verified boot and offscreen bitmap lifetime/packet smoke: 36 runs, 2,359,296 final RGB checks, zero errors; direct inbound packets 2048 -> 1024 per 1024 draws. No consistent elapsed-time gain; full acceptance pending.

- [x] Concurrent offscreen rendering baseline Beta6/V8/V9: 81 runs, 189 workers, 193,536 fills, 12,386,304 RGB checks; no errors; inspect fixed-work scaling and server locks next.

- [x] Fixed-work offscreen rendering comparison: 162 runs, 378 workers, 663,552 fills, 24,772,608 final RGB checks; same-team versus separate teams; first malformed-output campaign retained but excluded. Desktop shared read lock identified for instrumentation, no causal claim.

- [ ] V10 app_server opt-in per-window diagnostics: acquisition wall time for window/desktop read/write, dispatch and sync/fill/bitmap subsets; native build, boot and paired off/on acceptance pending.

- [x] V10 independent ZimaBlade full build, verified Mac import/boot, 12 paired smoke runs at batch64, 49,152 fills, 2,359,296 pixel checks, zero errors; 18 complete ON profiles, zero OFF. Full acceptance and causal diagnosis pending.

- [x] V10/Beta6 cold vs client/server buffer initialization, 36 runs, 147,456 timed fills and 9,437,184 RGB checks; V10 same-team first pass 46.515ms -> 5.415ms with server warm, no measured fault counts; full lifecycle and kernel counters pending.

- [x] V11b local boot and revision fix verified; 28 eligibility cases, 18 alternating OFF/ON lifecycle runs, 73,728 fills, 3,538,944 final RGB checks, zero errors; 27 warm records; full acceptance pending.

- [x] V11b two-surface batch64 extension: 12 runs, 49,152 fills, 1,572,864 RGB checks, no errors; lifecycle regresses despite faster rendering. Keep opt-in; V12 explicit completion acknowledgment candidate.

- [ ] V12 private opt-in server white-clear completion bit; client skips redundant fill only on validated acknowledgment. Native build, boot, correctness and lifecycle acceptance pending.

- [x] V12 local build 5581c34f, verified boot and 28 native eligibility cases; two matching server/client skip pairs, no incorrect activations. Lifecycle acceptance pending.
