# Explicit white bitmap lifecycle baseline, before V11
AI-assisted independent research fork. Beta6 and V10 (12b5c9ec),
same native binary SHA256. 4 vCPU/8 GiB HVF guests.
1/2/4 independent 256x256 RGB32 surfaces; threads vs separate teams;
4096 fills total, sync every 64, three repetitions. Explicit white
clear flag; each worker checks all 262144 bytes after constructor and
before view creation, then 65536 final RGB pixels after drawing.
36 runs, 84 worker rows, 147456 timed fills, 22020096 initial byte
checks and 5505024 final RGB checks, zero errors. No V11 implementation
in either guest. Setup includes client clear, full initial scan, view
creation and Sync, not pure allocation. Lifecycle begins at earliest
constructor start and ends at latest drawing Sync return; excludes
destruction, final scan, process start/exit. Not actual frames or FPS.
Host load uncontrolled, three repetitions; no performance claim.
Use same binary for V11 OFF/ON and inspect warm markers and negative
cases. V11 compile started on Zima separately; not yet validated.
