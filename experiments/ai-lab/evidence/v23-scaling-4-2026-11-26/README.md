# V23 four-stream scaling setting comparison
V22 image 4ae8e7ea; 4 vCPU/8192 MiB; synchronous rendering,
single-thread SD H264, observation counters ON.
Nearest/bilinear/bilinear/nearest, all four playback and diagnostic valid.
Complete observation bins: 19/19/20/19 seconds.
Draw completions 2270/2267/2368/2272. Zero fill timeouts.
Aggregate draws per second 4542/38 vs 4635/39; 15 vs 23
looper failures; 72/72 successful queries each treatment.
Original settings SHA verified restored; before and after each
trial the requested setting is confirmed. Effective bitmap scaling
geometry and filter execution not independently instrumented.
Not physical presentation FPS. Non-isolated host; no promotion.
