# Offscreen server/client buffer initialization experiment
AI-assisted independent research fork. Beta6 and V10 local 12b5c9ec,
same native binary checksum, HVF 4 vCPU/8 GiB. Four workers, 256x256
B_RGB32 bitmaps, 1024 timed FillRect each, Sync every 64, 3 repetitions
per topology and initialization condition. Cold does no explicit buffer
initialization, client memset writes whole bitmap before start barrier,
server warm does one full-surface FillRect plus Sync before barrier.
Final RGB verified after each worker's draws. 36 runs, 144 worker rows,
147456 timed fills, 48 extra warm fills, 9437184 final RGB checks,
zero errors. Marker absent (V10 profile off); spin default not re-read.
First pass makespan = latest first-256-fill Sync return minus earliest
worker start. Later metric = maximum per-worker duration after first
pass, not global makespan. Warm metric = maximum per-worker pre-barrier
initialization duration, not complete setup makespan. Do not simply add
warm and timed medians as total end-to-end latency.
V10 same-team median timed 57.103ms cold, 53.069ms client initialized,
23.673ms server initialized. First pass 46.515/30.802/5.415ms. Max warm
median 0/0.373/1.933ms. Separate-team V10 median timed
20.231/22.849/23.019ms. Beta6 same-team 36.078/38.444/24.463ms,
separate teams 50.072/53.127/25.739ms. Host load uncontrolled and
sample small. Server initialization changes residency, caches, work
ordering and potentially scheduling; no page-fault count measured.
Cannot infer actual page faults or a universal improvement. Do not
change public bitmap semantics or pre-touch all allocations. Static
inspection ClientMemoryAllocator uses B_NO_LOCK cloneable areas, may
resize chunks. Next isolate server-side faults versus drawing setup,
measure full lifecycle, then test narrowly bounded opt-in candidate.
