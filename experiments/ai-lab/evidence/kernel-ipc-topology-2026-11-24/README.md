# IPC topology experiment
AI-assisted independent research fork only. Haiku beta6 and V2
(d800dd54), QEMU/HVF, 4 vCPUs, 8 GiB. The same native executable
was compiled on beta6 and checksum-verified on V2. Four producer
threads and four receiver threads, 500 messages per producer.
One 64-slot shared port vs four separate 16-slot ports. Each
configuration was run three times per guest, with alternating order.
All 24,000 messages passed uniqueness and payload checks, all threads
joined, zero errors. Median elapsed times (microseconds):
beta6 shared 425060, independent 80615;
V2 shared 518121, independent 116365.
The experiment demonstrates a topology-dependent difference in this
virtualized workload, not a proven mutex bottleneck or bare-metal
speedup. Shared versus independent queues also change receiver
routing and wakeup behavior. The guest/host scheduling conditions
are not controlled; no speed attribution to kernel patches.
Next: instrument per-port locking, wait/wakeup and message allocation,
then decide whether a kernel change is justified. V3 still building.
