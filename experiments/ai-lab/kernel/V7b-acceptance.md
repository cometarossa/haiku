# V7b mutex handoff diagnostics (AI-assisted independent research fork)

V7b is a diagnostic candidate, not an optimization. On x86_64 the
existing untimed mutex slow path records queue entry and the timestamp
immediately before the existing thread_unblock call. The resumed
waiter records both intervals after thread_block returns B_OK.
Only mutexes named "translation map" participate (includes kernel maps,
unlike the V7a user-map counters). Timed waiters keep inactive sentinels;
the destroy/error path contributes no completed sample. No lock
ordering, ownership, mapping, or wakeup policy change.

KDL lab_mutexstats [on|off] exposes cumulative successful sample count,
invalid timestamp count, total queue and handoff-to-return time, and
>=50us / >=1ms bins. Default off. Before/after differences must be
monotonic; bins must satisfy long <= slow <= samples. Nonzero invalid
timestamps invalidate the corresponding timing window. The handoff
timestamp precedes thread_unblock and includes its scheduler work and
any subsequent dispatch delay; it is not a pure run-queue measurement.
Queue time includes preceding waiters and holder work. Spinlock entry
time is not measured by this command. Snapshots can split in-flight
operations; sample at quiescent boundaries. Global atomics and extra
stack fields can perturb timings.

Acceptance: verified image, separate overlay, default off, bounded
256/1024-page native vm_area_teams comparisons on 1/4 vCPUs, idle and
independent-team controls; >=3 repeats per configuration. Run V7a
lab_vmstats and V7b lab_mutexstats in the same windows, then disable
both. Repeat off/on and V7a baseline on HVF and TCG separately.
Verify IPC, scheduler and VM alias regressions. No bare-metal claim.
If handoff-to-return dominates, profile scheduler wake/dispatch;
if queue time dominates, examine holder chain/queue policy.
No broad mutex optimization without these checks.
