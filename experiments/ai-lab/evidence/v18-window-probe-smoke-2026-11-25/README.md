# V18 native persistent BMessenger smoke
V18 fb8c2e41, probe source d9c8b5b9. Verified binary and 120 s
320x180 H.264 fixture. One MediaPlayer window, no experimental
markers. All nine read-only scripting queries succeeded and positions
advanced 0 -> 466666 -> 933333 us. Both processes exit zero.
Smoke only; no paired comparison with hey or proof of multi-window
performance. Probe initialization measured separately. Next: matched
same-image workload with persistent query and native IPC sampling.
