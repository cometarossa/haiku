# Periodic scheduling wakeup under bounded CPU load
AI-assisted independent Haiku research fork only. Beta6 and V3
ai_7d5672a7; same binary verified by SHA256. Both use scheduler mode
0 (low latency). A normal or display-priority thread sleeps until
absolute deadlines spaced 5ms apart; zero or two normal-priority
CPU-bound workers pinned to the same vCPU 0. 120 samples per run,
three runs per configuration, 2880 samples total. All workers joined.
Lateness includes timer, scheduling and virtualization; it is not
isolated scheduler latency. If a deadline is missed, the next sample
keeps the original periodic grid (catch-up). Counts of lateness >=5ms
are therefore not independent events. Other VMs and host scheduling
uncontrolled. No native hardware or causal fork speedup claim.
