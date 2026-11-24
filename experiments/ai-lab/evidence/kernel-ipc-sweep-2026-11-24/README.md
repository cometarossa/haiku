# Kernel port capacity sweep and copy-error regression
AI-assisted independent research fork only. Same binaries compiled on
beta6 and transferred to V2 (d800dd54); checksums verified before V2 run.
QEMU/HVF, 4 vCPUs, 8 GiB. Shared port, 4 or 8 producers, 1000 messages
per producer, capacities 16/64/256. All 72,000 messages and shared
values verified across both guests. Single observations per condition;
not a controlled performance benchmark. Independent-port comparison
remains pending.
Both guests reproduced a false B_OK on write from an unreadable
userspace mapping. Queue stays empty, next legitimate write/read works.
Root cause: a local status declaration shadows the outer status in
writev_port_etc's user_memcpy failure branch. The patch propagates the
actual copy status to the existing cleanup path. Native post-fix
verification requires the rebuilt kernel; do not claim it passed yet.
