# V7b repeated HVF handoff windows
AI-assisted independent research fork. Revision 34258af0, CI 45444127880.
Six additional paired windows: two each of shared-team threads on
one or four vCPUs and independent teams on four vCPUs. Reverse order
in repetition 2. 256 pages/worker, same checksum-verified vmt binary.
24 worker rows, 12,288 additional alias/lifetime page checks passed,
zero invalid mutex timestamp samples. Combined summary includes the
prior smoke windows (one idle, one shared-team 4-vCPU, one independent
4-vCPU) from ../kernel-v7b-handoff-smoke-2026-11-24; do not count twice.
All paired deltas monotonic, histogram bins bounded, outer acquisition
and hold counts match; both samplers disabled after each window.
Shared-team contention reproduced in all three spread-vCPU windows;
queue and handoff-to-return times both elevated. System-wide counters,
different scope for VM and mutex samplers, uncontrolled host load,
debugger and transfer overhead. Queue time includes other waiters and
holder work; resume includes thread_unblock and scheduling delay.
No proof of scheduling root cause or bare-metal speed. Remaining gates:
1024-page repetition, 1-vCPU third repeat, idle repetition, matched
off/on V7b, TCG and IPC/scheduler/VM regression. No policy change.
