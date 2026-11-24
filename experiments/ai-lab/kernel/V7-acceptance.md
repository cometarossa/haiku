# V7a lock-hold diagnostics (independent research fork)
V7a is a diagnostic precursor, not a performance fix. Keep V5/V6
images and overlays unchanged. No lock ordering, ownership, page mapping
or TLB invalidation policy changes.

KDL lab_vmstats now reports outer acquisition durations and outer hold
durations through Flush, before mutex unlock; >=50us and >=1ms bins.
Only the virtual Lock/Unlock path is observed: direct recursive locking
of fLock in some paging operations is not covered. Time includes
preemption and instrumentation; threshold counts are not exact blocked
mutex counts. System-wide atomics may perturb results. An enable/disable
transition can split an interval; use snapshots outside workloads.

Acceptance:
- Build and verify image; boot isolated overlay, default counters off.
- Paired idle and workload windows, same binary, 1/4 CPU affinity,
  threads/independent teams, 256/1024 pages, >=3 repeats, alternate order.
- Compare V6 and V7a off/on, HVF and TCG separately; native test pending.
- Check monotonic counters and bins (>=1ms <= >=50us <= samples),
  hold/outer acquisition counts consistent in quiescent paired windows.
- Repeat IPC, scheduler, area lifecycle and alias coherence regressions.
- If waits dominate short holds, investigate mutex handoff/scheduling;
  if long holds dominate, profile work inside the critical section.
- Only then introduce an isolated, reversible optimization and repeat
  the same tests. Do not weaken TLB or mapping correctness.
