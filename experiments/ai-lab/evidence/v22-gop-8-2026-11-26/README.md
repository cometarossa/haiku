# V22 eight-stream GOP sensitivity
V21 image 2f9d27bf, 4 vCPU/8192 MiB. Single-thread H264 SD
fixed ON; deferred and speculative recovery OFF.
GOP 120/15/15/120; all trials diagnostic- and playback-valid.
GOP120 451/11625 vs GOP15 2/11861 producer fill timeouts;
8723 vs 9143 draws; 2247 vs 2403 looper failures;
89 vs 129 late consumer buffers. All 288 queries successful.
Position p95 first pair 326266->409694 us, second
202991->269421 us. Responsiveness worsens in both pairs.
Gap severity max 114 vs 7 frames; mean 44.77 vs 6.5
among rejected calls. All 451 long-GOP rejections occur in
first trial; the second pair has no rejections in either arm.
Different encodes differ in bitrate and decoded pixels.
Non-isolated host, lifetime counters, not presentation FPS.
Continue sixteen streams; no performance promotion.
