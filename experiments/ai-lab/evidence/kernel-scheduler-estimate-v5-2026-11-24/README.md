# V5 native scheduler latency estimator check
AI-assisted independent research fork. V5 ai_8f8e7d06; same executable
as the beta6/V4 estimator experiment, checksum checked in guest.
160 calls at priorities 5/10/15/20, zero or two bounded competing
workers on vCPU 0. Idle estimates 500 us (priority 20 also 1000 us);
all loaded estimates 1500 us. Previous 320 calls returned 100 us.
The degenerate behavior is no longer reproduced in these scenarios.
This validates responsiveness to tested load, not estimate accuracy,
real-time guarantees, priority monotonicity in live scheduling, or
Media Kit delivery. Previous IPC and media timing regressions pending.
V4 and V5 were restarted from verified cached images on Sequoia - Dati
after ACPI shutdown and storage migration; old overlays preserved.
