# Native thread handoff round-trip latency
AI-assisted independent research fork only. Haiku beta6 and V2
(d800dd54), same native binary compiled on beta6 and checksum-verified
on V2. Two normal-priority threads exchange one request and one reply
through two capacity-1 ports (zero-byte messages with sequence codes)
or two initially empty semaphores. Each run discards 20 warm-up rounds
and retains 500 timed round trips. Three repeats per mode and guest,
alternating order. 6000 measured rounds, all runs completed and joined.
Raw per-round samples retained. P95/P99 use nearest-rank pooled samples.
These are round-trip times including calls and scheduling, not isolated
context-switch or mutex latency; host load and CPU placement were not
controlled. Microsecond timer granularity limits precision.
Semaphores carry no payload or sequence metadata; comparison is for
signalling only, not a replacement for general IPC.
