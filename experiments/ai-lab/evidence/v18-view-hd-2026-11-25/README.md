# V18 native VideoView diagnostics HD
Same image fb8c2e41; 4/8-window balanced OFF/ON/ON/OFF.
All 8 trials pass. Recovery disabled throughout. 24 view lifetime
records in ON, zero in OFF. 4 HD: looper share 85.09/91.04%,
draw submission 8.85/4.44%. 8 HD: looper 51.27/53.40%,
draw submission 32.28/31.48%. Cumulative elapsed times, not CPU
or display presentation. 546 looper failures in 4363 non-null
8-window calls. Does not identify owner or establish port saturation.
Diagnostic overhead and scheduling may differ; 8-ON p95 scripting
347.5/395.4 ms vs OFF 207.7/232.9 ms. Do not claim acceleration.
Native completion and cleanup confirmed. Stable three VM PIDs.
Full screenshot sequence remains on host.
