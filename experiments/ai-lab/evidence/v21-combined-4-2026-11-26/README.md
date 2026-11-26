# V21 combined four-stream gate
Image 2f9d27bf, 4 vCPU/8192 MiB. Single-thread H264 SD fixed ON,
catch-up OFF; only deferred rendering toggled OFF/ON/ON/OFF.
All four trials pass diagnostic and playback checks, all decoder
records effective=1. OFF 5194 vs ON 5251 draw submissions;
84 vs 0 looper failures, zero fill timeouts both, 85 vs 91 late
consumer buffers. Position p95 OFF 1309/1050 us, ON 1319/6968 us.
ON notification mean queue time 2000.84 us; handler 47.81 us.
Lifetime counters, not actual FPS; two pairs, non-isolated host.
No overall performance acceptance. Gate for larger combined
campaign met. No new OS image; treatment remains opt-in.
