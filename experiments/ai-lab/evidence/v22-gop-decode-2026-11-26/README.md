# V22 GOP native correctness gate
V21 image 2f9d27bf, same native frame-digest binary; all 14400
frames and timestamps validated. One decoder thread fixed.
GOP120 2503318/2636984 us; GOP15 2660588/2787567 us.
Each fixture repeats its own pixel digests exactly. Different
encodes need not have identical pixels. Elapsed includes decoding,
hashing and initialization; not physical playback FPS.
Two pairs on non-isolated host; no causal generalization.
Native marker cleanup and RAMFS unmount confirmed.
