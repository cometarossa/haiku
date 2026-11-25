# V17 HD adaptive safety guard native validation
Image f960376e, same 720p H.264 fixture as V16 HD. Eight valid trials,
144 advancing playback samples, 432 individually timed scripting queries,
zero catch-up activations in all treatments. Both HD ON trials that
failed in V16 have valid counterparts here. Adaptive ON intentionally
excludes HD speculative decoding; this is safety validation, not HD
acceleration. Different runs and host scheduling confound cross-image
comparisons. Eight-window p95 command latency remains 225.8-559.0 ms.
Target calls are not physical presentation FPS. RAMFS cleanup and final
marker received. Exact guest and host runner sources retained. Full
screenshot sequence remains on host. Stable three QEMU processes.
