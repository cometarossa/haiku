# V2 native IPC and shared-area comparison
AI-assisted independent research fork only. Guest hrev60465+ai_d800dd54,
QEMU/HVF, 4 vCPU and 8 GiB. The executable compiled and run on beta6
was transferred to V2; V2 checked its SHA256 before execution.
All 13000 messages and shared values verified, zero errors.
The guest desktop image lacks g++, so no guest compilation on V2.
Timings are individual observations, not controlled performance
comparisons; multiple VMs were running and tests occurred at different
times. No attribution of speed differences to fork modifications.
The test uses threads in one team, not cross-team IPC.
