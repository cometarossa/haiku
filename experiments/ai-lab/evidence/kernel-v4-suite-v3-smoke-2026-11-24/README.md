# Unified V4 acceptance suite smoke test on V3
AI-assisted independent research fork. V3 ai_7d5672a7, same native
binaries previously compiled on beta6; checksums verified on host
and guest. One full suite run passed, including copy-error regression,
13000 port/shared-area messages, 4000 topology messages, 73728
nonblocking messages, 480 periodic wakeups and eight CPU workers.
Host was downloading the V4 image; other VMs were active. This is
a harness smoke test and correctness check, not the controlled
V3/V4 performance comparison. V4 build succeeded; guest validation
pending. Repeat the suite in alternating guest order.
