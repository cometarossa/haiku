# V22 sixteen-stream native observation
Image 4ae8e7ea, 4 vCPU/8192 MiB, single-thread SD H264.
Synchronous/deferred/deferred/synchronous; all four diagnostic
valid, zero playback valid. Nineteen complete seconds per trial.
Producer successful fills 6004 vs 12942; timeout 9486 vs 3967.
Draw completions 4381 vs 1499; looper failures 1574 vs zero.
Successful queries 38 vs 105 of 288. Zero-draw instance-seconds
284 vs 95 of 608. Quit-to-exit elapsed us
17651712/12471242/10091782/20877275.
Deferred treatment distributes completions more evenly but
reduces aggregate draw completions in both pairs. Completion
counts exclude setup and teardown; not presented frames.
Separate stages may cross bin boundaries. Non-isolated host.
No promotion of either rendering policy.
