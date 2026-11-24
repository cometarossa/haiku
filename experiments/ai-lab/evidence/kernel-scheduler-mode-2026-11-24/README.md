# Scheduler mode comparison on V3
AI-assisted independent Haiku research fork only. V3 ai_7d5672a7,
same wakeup executable as earlier comparison. Both binaries checked
in guest. Scheduler modes 0 (low latency) and 1 (power saving),
alternating mode order across three repeats, one-second settling delay.
Normal and display priorities, zero or two normal-priority CPU-bound
workers on vCPU 0; 120 samples per configuration per repeat, 2880 total.
Original scheduler mode 0 restored and read back successfully.
Lateness includes timer, scheduling and virtualization; other guests
and host scheduling uncontrolled. No energy or bare-metal claim.
