# V23 sixteen-stream scaling comparison
V22 image 4ae8e7ea, 4 vCPU/8192 MiB, synchronous rendering,
single-thread SD H264, observation counters ON.
Nearest/bilinear/bilinear/nearest, all four diagnostic-valid,
none playback-valid. Nineteen complete monotonic seconds per trial.
Successful fills 6851 vs 6544; timeouts 8708 vs 9124.
Draw completions 4964 vs 4685; looper failures 1858 vs 1827.
Successful queries 62 vs 41 of 288. Quit-to-exit elapsed us
41359926/20016620/26218781/34698522.
Original settings SHA restored and verified; settings before
and after each trial confirmed, effective bitmap path not
independently instrumented. Not physical presentation FPS.
Host not isolated. No performance promotion.
Next investigate app_server phases; do not reduce image quality.
