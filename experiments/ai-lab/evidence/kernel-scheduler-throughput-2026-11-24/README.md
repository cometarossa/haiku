# Scheduler CPU throughput baseline
AI-assisted independent Haiku research fork only. Beta6 and V3
ai_7d5672a7; same checksum-verified binary. Four normal-priority workers
pinned to one or four virtual CPUs, three repeats, nominal common
one-second measurement interval. Count dependent xorshift steps,
1024 per batch. All 48 completed worker rows independently checked
against the expected xorshift digest by GF(2) exponentiation.
Jain fairness index calculated on equal-priority worker counts; 1
means equal completed work. Start delays and end overshoot included
in raw data. Initial incomplete beta run retained separately; the
probe was revised to tolerate a start deadline already reached and
emit explicit errors. Exact cause of original incomplete run unknown.
Final 12 runs complete with no reported worker errors.
This is a synthetic VM workload, not hardware throughput or an
isolated context-switch measurement. Host load not controlled.
V4 comparison pending; do not infer causal V3 speed changes.
