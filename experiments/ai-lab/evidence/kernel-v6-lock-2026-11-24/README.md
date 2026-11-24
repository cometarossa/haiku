# V6 preliminary diagnostic evidence
AI-assisted independent research fork, 2026-11-24. Revision 2e4aa9f5.
Source: guest serial logs; extracted lines only. Counters are cumulative
and system-wide, not per-workload or per-team measurements.

Observed on HVF: two consecutive instrumented windows had lock-wait
deltas 8,938,603 us and 8,826,144 us. The corresponding flush time
deltas were 3,484 us and 84 us. The next window had lock-wait delta
1,401 us. This supports investigating lock acquisition/handoff rather
than presuming TLB invalidation is the dominant cost.
TCG also reproduced the shared-address-space slowdown, but absolute
timings are not directly comparable. Host load was uncontrolled.
Full matched idle, on/off, and native regression tests remain pending.
