# Concurrent offscreen app_server rendering baseline
AI-assisted independent research fork. Beta6, V8, V9 HVF guests,
4 vCPU / 8 GiB. Same checksum-verified native executable. One application
team with one, two or four threads, each rendering to an independent
256x256 bitmap through its own offscreen window. Barrier releases
workers together, actual start skew retained. Each worker draws 1024
rectangles, Sync every 1/64/1024 fills. 81 runs, 189 worker rows,
193,536 fills and 12,386,304 final RGB pixel checks, zero errors.
Timing is earliest worker start to latest final Sync return, not CPU
time or frames per second; throughput is n*1024 / makespan. No CPU
affinity or actual overlap guarantee. Final pass only checked.
Host load uncontrolled, sequential guests, three repeats; notable
variation especially at large batches. V9 bitmap coalescing does not
directly affect FillRect; no attribution of timing differences to V9.
Not onscreen compositing, GPU or bare-metal evidence. Next compare
fixed total work and separate processes, inspect server drawing locks
and scheduler interference before proposing a tuning patch.
