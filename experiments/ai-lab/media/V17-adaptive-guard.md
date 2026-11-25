# V17 conservative recovery guard

V16 HD: both 8-window OFF runs validated (~8 s observation), both ON
runs failed playback/control responsiveness (~46-47 s). Recovery
activation and fewer fill timeouts do not establish a performance win.
This does not isolate decoder overhead from drawing/looper contention.

V17 keeps default behavior unchanged and retains the V16 treatment for
controlled comparison. With both haiku-lab-media-catchup and
haiku-lab-media-catchup-adaptive markers present, speculative catch-up
is permitted only for positive raw dimensions up to 307200 pixels.
After an unsuccessful recovery read or a recovery attempt exceeding
4 ms, back off for 100 ms per supplier. Track replacement resets backoff.
These thresholds are conservative experiment choices, not an optimized
policy. No hard deadline is promised: one decoder read can block.
Forced generation and ordinary short-gap handling stay unchanged.
HD treatment intentionally falls back to baseline, not an HD speedup.

Tests exercise actual FillBuffer method with fake track: existing V16
semantics, HD exclusion, slow-read backoff and expiry, error backoff,
guard-only disabled, forced generation. Native acceptance: 8 SD
retains improvement without control delay; HD guarded is no worse than
baseline; confirm guard and recovery behavior with real decode and
GUI timing. Measure actual displayed frame correctness separately.
