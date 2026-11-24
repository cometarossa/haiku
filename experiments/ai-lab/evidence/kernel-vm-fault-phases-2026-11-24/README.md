# Phased anonymous area first-touch baseline
AI-assisted independent research fork. Beta6 and V5 ai_8f8e7d06,
same native executable with SHA256 verified in V5. Four workers
in one team on one or four vCPUs with verified affinity and phase
barriers separating creation, first access, second access,
resident verification and deletion. In read mode first read checks
zero contents at page ends, second writes patterns; write mode
first writes patterns, second checks them. Both verify patterns
again before deletion. Three repeats per configuration.
72 runs, 288 worker rows, 129024 successful page checks in final
resident verification, zero reported errors. Wall-clock per-worker
medians, not raw page-fault durations or aggregate throughput.
The first-touch delay is reproduced even without interleaved area
creation/deletion, cloning or initial writes. Further work should
measure lock acquisition, fault phases and actual invalidation
cost; host/QEMU/HVF effects remain uncontrolled. No kernel tuning
change in this experiment. V6 diagnostic build pending.
