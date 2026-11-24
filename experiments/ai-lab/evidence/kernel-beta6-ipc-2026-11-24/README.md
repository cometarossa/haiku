# Native kernel IPC and shared-area baseline
AI-assisted independent research fork only. Haiku R1/beta6 in QEMU/HVF,
4 vCPU, 8 GiB, existing disposable baseline overlay. Compiled
experiments/ai-lab/kernel/port_area_smp.cpp with native g++.
One, four, eight producer threads each send 1000 sequence-checked
messages via a capacity-16 kernel port. Each producer writes a disjoint
slice of a cloned shared area. The receiver verifies per-producer
ordering, payloads, join status, shared memory and empty-read timeout.
All 13,000 messages and values verified. No errors.
This is a same-team multithreaded kernel-port test, not cross-process
IPC or a scheduler throughput benchmark. Timings are descriptive only:
several VMs ran on the same host. V2 comparison remains pending.
