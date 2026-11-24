# V7a paired lock diagnostic windows (HVF)
AI-assisted independent research fork, 2026-11-24. Guest revision
93d9c2d1; 4 vCPUs, 8 GiB. Same checksum-verified vm_area_teams
binary used on beta6/V5. Three repetitions per condition: idle
(2 s guest sleep), four threads on one vCPU, four threads on four
vCPUs, four independent teams on four vCPUs. 1024 pages per worker.
Order reversed in repetition 2. 12 windows, 9 benchmark runs,
36 worker rows, 73728 alias/lifetime page checks passed.
Before/after KDL snapshots preserve complete cumulative counters.
Parser verified monotonicity, histogram bounds, matching outer
acquisition/hold sample counts per window. Counters off after run.
All timings are cumulative across system-wide sampled user maps;
they include shell, debugger transition, transfer and background
activity, not exact workload-only attribution. The active window
duration is not identical across conditions; host load uncontrolled.
This is a bounded HVF diagnostic experiment, not the complete
acceptance gate or bare-metal evidence. No V7 optimization yet.
The shared-team spread-vCPU windows reproduce high outer-lock wait
durations despite short observed hold durations and little flush time.
The independent-team controls show dramatically lower wait time.
Investigate mutex queue handoff / wake scheduling and spinlock entry
before modifying synchronization semantics. V7a off/on comparison,
256-page cases, separate TCG paired windows and regression suite
remain pending.
