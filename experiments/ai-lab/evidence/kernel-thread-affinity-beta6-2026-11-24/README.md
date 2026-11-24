# Native thread-affinity handoff baseline
AI-assisted independent research fork only. Haiku beta6 on QEMU/HVF.
Private kernel syscall ABI used because the guest GNU compatibility
headers were unavailable. Affinity masks read back and current vCPU
checked at the beginning of each round on both threads.
CPU 0/0 versus CPU 0/1, semaphore or zero-payload port round trips,
three runs of 500 measured rounds per configuration after warmup.
6000 completed samples. Fixed configuration order, host load uncontrolled;
virtualized round-trip latency only, not isolated context-switch time.
V2/V3 comparison pending. No scheduler patch or speedup claimed.
