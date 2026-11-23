# Concurrent video decode baseline — 2026-11-24

AI-assisted independent research fork only. Native Haiku R1/beta6
under QEMU/HVF, four virtual CPUs, 8 GiB RAM, disposable baseline
QCOW2 overlay. Original disk untouched. Existing native media_decode
binary and 150-frame 1280x720 H.264 fixture were used unchanged.

Two then four separate decoder processes were launched concurrently.
All six exited zero and each decoded 150 frames, with active pixel
FNV-1a digest 8c82dcfcda88175a matching the single-decoder reference.
900 decoded frames total. CSV transferred from the guest via a bounded
localhost HTTP receiver. Screenshot records the native terminal output.

This is correctness evidence, not simultaneous GUI playback, frame rate,
CPU utilization, dropped-frame measurement or a bare-metal benchmark.
The full fork-built desktop is still being compiled separately.
