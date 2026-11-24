# V6 diagnostic acceptance (AI-assisted independent Haiku fork)

V5 remains the performance candidate. V6 is diagnostic, not a tuning
patch. No change to page mapping, lock ownership or invalidation policy.
The x86-64 Map path installs absent entries without invalidating the TLB;
measure rather than presume remote invalidations cause first-touch delays.

- Compile regular x86_64 desktop and verify image checksums; use isolated
  overlay on Sequoia via existing image-storage alias. Verify V6 revision.
- Confirm counters default off in kernel debugger (KDL), command
  lab_vmstats. Command with on/off changes sampling only. Do not reset
  counters: use cumulative snapshot differences. Continue guest normally.
- Capture idle window plus identical native vm_area_teams binary runs,
  separately for threads and independent teams, 1 and 4 vCPUs, three
  repeats, alternating order. Preserve raw timings, KDL output and
  host conditions. Include warm resident-page control.
- Compare V6 off vs V5 and V6 on vs off. Re-run IPC and scheduler
  correctness suite and page-alias lifecycle checks. Do not accept
  performance regressions as improvements; disable counters after tests.
- Counters are system-wide user translation-map observations, not
  per-team totals. Lock time includes uncontended and recursive calls;
  flush time includes local work and possible interprocessor wait.
  Remote_candidates is a separate active-CPU snapshot, not an exact IPI
  count. Empty flush is not an invalidation. Counts may include unrelated
  system activity or operations spanning enable/disable boundaries.
- Global atomics and timing calls perturb the measured paths when enabled.
  KDL stops guest CPUs and can affect timings; collect snapshots outside
  the timed workloads. Compare differences only; no hardware claims.
- If the counters cannot explain the first-touch gap, instrument the
  actual remote branch and page-fault phases separately. Do not relax
  TLB correctness based on elapsed-time correlation alone.
