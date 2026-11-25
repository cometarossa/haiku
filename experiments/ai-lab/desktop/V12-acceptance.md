# V12 single white initialization experiment
AI-assisted independent fork. Private allocation reply bit 0x8 indicates
a completed full server white fill; no new message fields or public ABI.
V11 marker retains redundant clear; separate marker
/boot/home/config/settings/haiku-lab-bitmap-single-clear enables V12.
Both absent by default. Existing lab signature retained for identical
binary comparisons. New server verifies allocator, flags, RGB32, <=1 MiB,
area bounds, exact row size and extent before acknowledging. New client
skips only after a successful mapping and valid reply fields with exact
allocator+ack bits, expected flags/color/size. Old server sends no bit;
old client ignores bit and still clears. Reconnect, malloc, overlay and
noneligible allocations retain original paths. Mixed-version behavior
requires verification, not assumed tested. Logs distinguish server ack
and actual client skip, matching team/token/length. Logs add overhead.
Acceptance: isolated boot; 28 eligibility cases including ordinary,
same binary, off/V11/V12, 1/2/4 surfaces, threads/teams, batch64 then
1/1024; byte/pixel validation; zero ack/skip when disabled or excluded;
matching exactly one ack+skip per eligible allocation; cleanup markers.
Add padded row, CMAP8, no-server-link, clone, overlay and churn tests.
Do not enable globally or claim benefit until repeated complete lifecycle
and pressure/desktop regression tests pass. No page fault attribution.

## Lifecycle measurement correction
The original native binary measured from worker 0 setup_start, not the
earliest setup_start across workers. Rendering makespan and byte/pixel
validation remain valid. Historical lifecycle medians are provisional
worker-0-origin values; never silently replace their raw evidence.
The corrected source takes the minimum over workers. Recompile into a
separate hashed binary and repeat same-image OFF/V11/V12 comparisons.

## Optional setup attribution probe
Compile a separate native binary with -DLAB_SETUP_PHASES (same source,
compiler and optimization), hash it independently; run --three-way
--setup-phases --binary-dir <new-directory>. Five extra fields per worker:
constructor, lock, initial white scan, view attach/setup, first Sync.
All are wall-clock durations, nonnegative and sum exactly to setup time.
Preserve per-worker data; maxima for different workers are not additive.
This measures client-visible phases, not CPU cost or page fault counts.
Diagnostic timestamps and existing serial logs can perturb timing.
Do not mix with uninstrumented performance evidence. Native compile and
execution still pending.
