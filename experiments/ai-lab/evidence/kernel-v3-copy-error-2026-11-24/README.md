# V3 kernel IPC regression passed
AI-assisted independent research fork. CI build 45302538749, revision
7d5672a7. Both compressed and raw image hashes verified on boot;
separate QEMU/HVF overlay, 4 vCPUs, 8 GiB. Desktop and Terminal reached.
Same binary used on beta6 and V2 was checksum-verified before execution.
Previously B_OK on unreadable buffer; now B_BAD_ADDRESS as expected.
Queue remained empty and next legitimate write/read succeeded.
This verifies the specific fix, not general kernel stability or speed.
