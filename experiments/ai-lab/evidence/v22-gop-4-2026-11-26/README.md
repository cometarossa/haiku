# V22 four-stream GOP sensitivity
V21 image 2f9d27bf, 4 vCPU/8192 MiB. Single-thread H264 SD
fixed ON; deferred and speculative recovery OFF.
GOP 120/15/15/120; all trials diagnostic- and playback-valid.
GOP120 46/5456 vs GOP15 0/5436 gap timeouts;
5175 vs 5278 draws; 141 vs 59 looper failures;
32 vs 38 late consumer buffers. All 144 queries successful.
Position p95 first pair 313413->933 us, second 863->3192 us.
Only first long-GOP trial has gap timeouts; effect not yet
replicated across both pairs. Different encodes differ in
bitrate and decoded pixels, non-isolated host, lifetime counters.
Not presentation FPS. Four-stream gate passed; continue eight.
