# V22 sixteen-stream GOP sensitivity
V21 image 2f9d27bf, 4 vCPU/8192 MiB. Single decoder thread ON,
deferred rendering and speculative recovery OFF; GOP120/15/15/120.
All four diagnostic-valid, zero playback-valid.
GOP120 24078/39273 vs GOP15 3287/65731 fill timeouts;
11357 vs 45186 lifetime draw submissions, 3075 vs 15738
window lock failures, 73 vs 3 successful queries out of 288.
Final upload delays are very different. Counts span teardown;
no actual exit timestamps or observation-phase draw counters.
Do not infer increased display throughput from raw counts.
See ../../media/V22-teardown-audit.md. New report deliberately
withholds normalized draw rates. Host not isolated.
Different encodes differ in bitrate and decoded pixels.
No performance acceptance. Preserve the failed playback evidence.
