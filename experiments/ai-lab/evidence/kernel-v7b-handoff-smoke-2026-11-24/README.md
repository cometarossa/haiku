# V7b HVF boot and handoff smoke test
AI-assisted independent research fork, 2026-11-24. Revision 34258af0,
CI 45444127880. Compressed and raw image hashes checked by regular
boot helper; separate QCOW2 overlay on Sequoia, 4 vCPU, 8 GiB.
Desktop and kernel debugger verified. Both sampling groups default
off with zero counters. Identical checksum-verified native vmt binary.
Three windows: idle (2s guest sleep), four shared-team threads on
four vCPUs, four independent teams on four vCPUs. 256 pages/worker.
Two completed benchmark runs, eight workers, 4096 alias/lifetime
checks, zero invalid mutex timestamp samples. Both counters disabled
after each window. Complete paired snapshots and raw outputs retained.
System-wide cumulative user map counters and named mutex counters
(including kernel maps) have different coverage; do not equate them.
Queue-to-handoff and handoff-to-return are not pure scheduler timings;
global atomics, guest and host activity, KDL boundaries affect them.
Single sample per workload, not a completed acceptance or performance
claim. Repeat matched 1/4 CPU, 256/1024 pages, off/on and TCG cases,
regression suite before tuning. No lock-policy change.
