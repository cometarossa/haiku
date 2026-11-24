# Anonymous area shared vs independent address spaces
AI-assisted independent research fork. Beta6 and V5 ai_8f8e7d06,
same checksum-verified binary. Four workers in one team (threads)
or four forked teams, each with independent areas and aliases.
One or four vCPUs, verified affinity and residency, three repeats
per condition. Different start barriers for threads and teams,
outside the timed page operations. 72 completed runs, 288 worker
rows, 258048 page-level alias checks, no errors.
Large first-touch slowdown reproduced in shared-team spread-vCPU
case, much smaller in independent teams. Consistent with shared
translation-map/address-space contention or interprocessor
synchronization; not direct proof of TLB invalidation as cause.
X86VMTranslationMap::Unlock calls Flush before final unlock;
Flush can issue synchronous invalidation to active CPUs through
VMTranslationMap::InvalidateTLBList/InvalidateUserTLB.
Inspect actual first-touch Map path and count events before
changing invalidation rules. Host scheduling and HVF overhead
remain uncontrolled. No kernel patch or bare-metal claim.
