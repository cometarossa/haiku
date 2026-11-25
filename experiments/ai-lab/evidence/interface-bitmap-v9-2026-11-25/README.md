# V9 bitmap synchronous draw coalescing: native guest smoke
AI-assisted independent research fork. V9 87d37528 / CI 45504533141.
Verified compressed/raw hashes, independent overlay, desktop and terminal
boot on Sequoia, QEMU/HVF 4 vCPU / 8 GiB. Beta6 and V8 controls, V8 spin
last confirmed off; V9 default off. Two separately compiled native test
binaries, each checksum-verified and identical across guests. 36 runs,
36,864 synchronous draws, 2,359,296 final RGB pixel checks, no errors.
Immediate source-memory overwrite after each draw, four overloads,
both transaction states. Only final pixels are checked; intermediate
passes and invalid-argument barrier semantics are not independently
verified. Packet test identifies the unique newly created offscreen port
and uses total_count delta with an empty queue before and after timing.
All three direct runs: Beta6/V8 2048 packets, V9 1024. Transaction
control 1024 throughout. Confirms 50% reduction in inbound port packets
in the tested path, not total system IPC. Timing change not consistent
across the two test binaries, no established speedup. Host load
uncontrolled; no GPU, screen compositing, native-hardware claims.
Remaining gates: onscreen, clipping/scaling, picture recording, deletion,
boundary cases, regression tests, controlled repeat timing.
No new OS code in this commit. Keep previous images.
