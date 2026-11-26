# V23 eight-stream scaling setting comparison
V22 image 4ae8e7ea; 4 vCPU/8192 MiB; synchronous rendering,
single-thread SD H264, observation counters ON.
Nearest/bilinear/bilinear/nearest, all four playback and diagnostic valid.
19 complete monotonic seconds per trial. Draw completions
3774/3744/3639/3710. Zero fill timeouts in observation.
Aggregate draws 7484 vs 7383 over 38 seconds per treatment.
Looper failures 1611 vs 1722; 144/144 successful queries each.
Position p95 us 1323/106031/181501/75632; both pairs worsen
with bilinear setting. Quit-to-exit us
3231961/3047170/3005847/3391859.
Original settings SHA verified restored; before and after each
trial requested setting confirmed. Effective bitmap geometry
and filter execution not independently instrumented.
Not physical presentation FPS. Non-isolated host; no promotion.
