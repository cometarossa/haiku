# V22 native diagnostics ON smoke
Image 4ae8e7ea; fixed single-thread SD H264, 4 vCPU/8192 MiB.
Synchronous/deferred/deferred/synchronous, four streams.
All 4 diagnostic- and playback-valid, 144/144 queries successful.
19 complete monotonic seconds per trial; draw completions
2255/2280/2281/2275. Window lock failures 7/0/0/5.
Zero producer fill timeouts within complete observation bins.
All lifetime conservation and fill-time checks pass.
A completion may cross an interval boundary; not physical FPS.
Quit-to-exit us 581722/615683/601195/608465.
Non-isolated host; no claim of zero overhead versus OFF.
