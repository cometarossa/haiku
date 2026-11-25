# V16 native catch-up A/B
Image a1b69d83; same hashed 320x180 silent moving clip; balanced OFF/ON
order 4 and 8 windows; both V15 stats and overlay preflight always ON.
8/8 exit zero; 144/144 playing queries with advancing per-window position.
78 host samples with the same 3 QEMU PIDs. All records pass conservation.
Four-window trials have zero fill timeouts with or without recovery;
no activation at this load, so no demonstrated recovery benefit.
Eight-window first pair: 596/3410 (17.48%) OFF vs 44/3417 (1.29%) ON;
5 recovery activations, 2766 vs 3333 target calls, observation 8.049
vs 8.051 s, producer late fraction increased ~1.33 percentage points.
Second pair: 527/4441 (11.87%) OFF vs 1/4964 (0.02%) ON;
1 activation, observation 12.453 vs 13.831 s due to slow queries.
Second pair is not duration-matched and raw target-call comparison
is confounded. Counts span whole node lifetimes, including startup/stop.
No send errors; buffer reclaim warnings remain in every trial.
No physical FPS or image-correctness assertion. Host not isolated.
Retain opt-in status pending repeats with phase timing and correctness
checks including seek, audio, cover art and longer/higher-res footage.
Raw full screenshot sequence retained on host at guest-results source.
