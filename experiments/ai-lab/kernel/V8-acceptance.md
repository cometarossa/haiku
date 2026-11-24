# V8 bounded translation-map trylock (AI-assisted independent research fork)

First opt-in performance candidate after V7 diagnostics. Only x86_64
user translation-map Lock() calls on SMP may try existing recursive
trylock before taking the ordinary blocking path. Initial try plus
at most 64 retries, with PAUSE and an elapsed-time check before each
retry; nominal retry budget 8 us. No hard realtime bound: preemption,
trylock's internal spinlock and instrumentation can extend elapsed time.
No change to Unlock, TLB invalidation, mapping or generic mutex policy.
Existing queued ownership is preserved by trylock's holder/count check.
New arrivals may compete before entering the queue; fairness, priority
inversion and CPU consumption must still be tested. On the same CPU or
a descheduled owner, bounded spinning can waste CPU time. Default OFF.

KDL lab_vmspin [on|off]: cumulative contended initial attempts, retry
successes, blocking fallbacks, elapsed retry time. Fast initial successes
are deliberately not counted. At quiescent boundaries:
contended == acquired + fallback. Use snapshot differences, not reset.
Sampling overhead included in active policy. Disable after experiments.

Acceptance before considering default enablement:
- Build/boot verified separate overlay, check revision/default off;
  compare V8 off vs V7b off using same native executable.
- Alternate V8 off/on, 3+ paired repetitions for 256/1024 pages,
  same vs independent teams, same/split vCPU. Keep other diagnostics off
  during timing runs. Capture idle, CPU throughput, fairness, long-tail
  wait/wakeup and IPC regressions with both modes; repeat mixed-priority
  workloads and memory lifetime/alias checks. Separate HVF and TCG.
- Inspect retry success/fallback counts and time, not only wall time.
  Reject on correctness error, starvation, substantial CPU regression,
  or no reproducible benefit. Keep default off without native validation.
- No universal or bare-metal performance claims. Host activity matters.
