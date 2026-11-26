# V21 eight-stream decoder parallelism
Image 2f9d27bf; 4 vCPU, 8192 MiB. Four balanced trials, all
diagnostic- and playback-valid. Deferred rendering and catch-up OFF.
OFF 914/11372 fill timeouts; ON 89/11340. All are frame-gap
timeouts. Draw submissions 8486 vs 9217, lock failures 1703 vs 1816.
First pair 87 vs 89 timeouts; second 827 vs 0. Large run variation,
not a consistently replicated effect. Position p95 improves in first
pair but worsens in second. Controller timelines advance near realtime;
screens 023 and 025 confirm visual advancement, not constant FPS.
Lifetime counters include setup/teardown; host not isolated.
Default remains OFF. Continue sixteen-stream characterization.
